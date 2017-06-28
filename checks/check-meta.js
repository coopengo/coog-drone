'use strict'

const axios = require('axios')

const ALLOWED_PROJECTS = {
  'coopengo/coog': [
      [1, 'Coog'],
      [29, 'Coog-Tech'],
      [31, 'Maintenance Coog'],
      [37, 'Code rewriting']
  ]
}

const githubUri = `https://api.github.com/repos/coopengo/${process.env.DRONE_REPO_NAME}/pulls/${process.env.DRONE_PULL_REQUEST}`
const redmineUri = 'https://support.coopengo.com'

const githubParams = {
  params: {
    access_token: process.env.GITHUB_TOKEN
  }
}

const _throw = (msg) => {
  throw new Error(msg)
}

const getData = () => {
  return new Promise((resolve, reject) => {
    axios.get(githubUri, githubParams).then(({data}) => {
      resolve(data)
    }).catch((err) => {
      reject(err.message)
    })
  })
}

const getLabels = (json) => {
  return new Promise((resolve, reject) => {
    axios.get(`${json._links.issue.href}/labels`, githubParams).then(({data}) => {
      resolve(data.map((elem) => { return elem.name }))
    }).catch((err) => { throw new Error('[Labels] ' + err) })
  })
}

const checkTitle = (json) => {
  const title = json.title

  !title.includes(': ')
      ? _throw('Title should be "<module>: <short title>"')
      : title.slice(-3) === '…'
          ? _throw('Title should not end with "…"')
          : console.log('Title is ok.')
}

const getRedmineRef = (body) => {
  if (body.includes('Fix #') || body.includes('Ref #')) {
    const lines = body.trim()
    const lastLine = lines.split('\n').slice(-1)[0]
    if (!(lastLine.slice(0, 5) === 'Fix #' || lastLine.slice(0, 5) === 'Ref #')) {
      throw new Error('Malformed redmine issue reference')
    }

    return {
      type: lastLine.slice(0, 3),
      issue: lastLine.slice(5)
    }
  }
  throw new Error('Missing redmine issue reference.')
}

const checkRedmineRef = (body) => {
  const ref = getRedmineRef(body)
  console.log(`Redmine issue identified as ${ref.type} #${ref.issue}.`)

  const lines = body.trim().split('\n')
  lines.length === 1
    ? console.log('Body seems ok.')
    : lines.splice(-2, 1)[0] === '\r'
      ? console.log('Body seems ok.')
      : _throw('Missing empty line before redmine reference')
}

const checkBody = (json) => {
  const body = json.body

  !body
    ? _throw('Body is empty.')
    : checkRedmineRef(body)
}

const checkRedmineIssue = (json, labels) => {
  const ref = getRedmineRef(json.body)

  axios.get(`${redmineUri}/issues/${ref.issue}.json`, {
    auth: {
      username: process.env.REDMINE_TOKEN,
      password: ''
    }
  }).then(({data}) => {
    const issue = data.issue

    if (labels.includes('bug')) {
      if (ref.type === 'Fix' && !issue.tracker.id === 1) {
        throw new Error(`Issue ${ref.issue} is not a bug!`)
      } else if (ref.type === 'Ref' && ![2, 3].includes(issue.tracker.id)) {
        throw new Error(`Ref ${ref.issue} is not a feature!`)
      }
    }
    if (labels.includes('enhancement')) {
      if ([2, 3].includes('issue.tracker.id')) { throw new Error(`Issue ${ref.issue} is not a feature!`) }
    }
    if (!ALLOWED_PROJECTS[json.base.repo.full_name].map((x) => { return x[0] }).includes(issue.project.id)) {
      throw new Error(`Bad project for issue ${ref.issue}.`)
    }
    if ((labels.includes('bug') && !labels.includes('cherry checked')) === true) {
      throw new Error('Missing cherry check.')
    }

    console.log("Everything's fine here.")
  }).catch((err) => {
    err.response.status === 404
      ? _throw('Issue seems not to exist: ' + err.response.status)
      : _throw('Could not reach Redmine\n' + err.message)
  })
}

const checkLabels = (json, labels) => {
  labels.includes('bug') && labels.includes('enhancement')
    ? _throw('Cannot have both "bug" and "enhancement" label')
    : !labels.includes('bug') && !labels.includes('enhancement')
      ? _throw('No bug or enhancement labels found')
      : checkRedmineIssue(json, labels)
}

const getIssuesFromLogs = (logs) => {
  const result = []

  logs.forEach((log) => {
    if (log.includes('* FEA#')) result.push({number: log.split('* FEA#')[1].slice(0, 4), type: 'FEA'})
    if (log.includes('* BUG#')) result.push({number: log.split('* BUG#')[1].slice(0, 4), type: 'BUG'})
    if (log.includes('* OTH: ')) result.push({type: 'other', number: ~~Math.random() * 100})
  })

  return result
}

const checkIssues = (issues, labels) => {
  return new Promise((resolve, reject) => {
    for (let i = 0, l = issues.length; i < l; ++i) {
      axios.get(`${redmineUri}/issues/${issues[i]}.json`, {
        auth: {
          username: process.env.REDMINE_TOKEN,
          password: ''
        }
      }).then(({data}) => {
        if (issues[i].type !== 'other') {
          const issue = data.issue

          if (labels.includes('bug')) {
            if (issues[i].type === 'BUG' && !issue.tracker.id === 1) {
              reject(new Error(`Issue ${issues[i].number} is not a bug!`))
            } else if (issues[i].type === 'FEA' && ![2, 3].includes(issue.tracker.id)) {
              reject(new Error(`Ref ${issues[i].number} is not a feature!`))
            }
          }
          if (labels.includes('enhancement')) {
            if ([2, 3].includes('issue.tracker.id')) {
              reject(new Error(`Issue ${issues[i].number} is not a feature!`))
            }
          }
          if ((labels.includes('bug') && !labels.includes('cherry checked')) === true) {
            reject(new Error('Missing cherry check.'))
          }
        }
      }).catch((err) => {
        err.response.status === 404
          ? reject(new Error('Issue seems not to exist: ' + err.response.status))
          : reject(new Error('Could not reach Redmine\n' + err.message))
      })
    }
  })
}

const checkContents = (json, labels) => {
  return new Promise((resolve, reject) => {
    axios.get(`${json._links.self.href}/files`, githubParams).then(({data}) => {
      if (data) {
        data.forEach((file) => {
          const filename = file.filename
          const patch = file.patch
          if (filename.includes('CHANGELOG')) {
            console.log(`CHANGELOG file detected in ${filename}.`)

            const logs = patch.split('\n').filter((log) => { return log.includes('* FEA#') || log.includes('* BUG#') || log.includes('* OTH:') })

            if (logs.length === 0) reject(new Error('Malformed logs. No FEA, BUG or OTH detected in CHANGELOG.'))

            const issues = getIssuesFromLogs(logs)

            checkIssues(issues, labels).catch((err) => { reject(err) })

            resolve('CHANGELOGs seem ok.')
          }
        })
      } else {
        reject(new Error('Pull request is empty!'))
      }
      reject(new Error('No CHANGELOG file detected.'))
    }).catch((err) => {
      reject(err)
    })
  })
}

const main = () => {
  getData().then((json) => {
    process.RAW_JSON = json
    return getLabels(json)
  }).then((labels) => {
    const arg = process.argv[2]

    const checks = {
      'title': checkTitle,
      'body': checkBody,
      'content': checkContents,
      'label': checkLabels
    }

    if (labels.includes(`bypass ${arg} check`)) {
      console.log(`${arg} forced.`.toUpperCase())
    } else {
      switch (arg) {
        case 'label':
          checks[arg](process.RAW_JSON, labels)
          break

        case 'content':
          checks[arg](process.RAW_JSON, labels)
            .then((msg) => { console.log(msg) })
            .catch((err) => {
              console.log(err)
              process.exit(1)
            })
          break

        case 'tests':
          process.exit(1)

        default:
          checks[arg](process.RAW_JSON)
          break
      }
    }
  }).catch((err) => {
    console.log(err.message)
    process.exit(1)
  })
}

main()
