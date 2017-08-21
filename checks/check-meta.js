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
  return
    title.includes(': ')
      ? 'Title should be "<module>: <short title>"'
      : title.slice(-3) === '…'
        ? 'Title should not end with "…"'
        : true
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

const checkBody = (json) => {
  const body = json.body

  const ref = getRedmineRef(body)
  console.log(`Redmine issue identified as ${ref.type} #${ref.issue}.`)

  return body
    ? true
    : 'Body is empty.'
}

const checkLabels = (json, labels) => {
  const ref = getRedmineRef(json.body)

  return new Promise((resolve, reject) => {
    axios.get(`${redmineUri}/issues/${ref.issue}.json`, {
      auth: {
        username: process.env.REDMINE_TOKEN,
        password: ''
      }
    }).then(({data}) => {
      const issue = data.issue

      labels.includes('bug') && labels.includes('enhancement')
        ? reject(new Error('Cannot have both "bug" and "enhancement" label'))
        : !labels.includes('bug') && !labels.includes('enhancement') & reject(new Error('No bug or enhancement labels found'))


      if (labels.includes('bug')) {
        if (ref.type === 'Fix' && !issue.tracker.id === 1) {
          reject(new Error(`Issue ${ref.issue} is not a bug!`))
        } else if (ref.type === 'Ref' && ![2, 3].includes(issue.tracker.id)) {
          reject(new Error(`Ref ${ref.issue} is not a feature!`))
        }
      }
      if (labels.includes('enhancement')) {
        if ([2, 3].includes('issue.tracker.id')) { reject(new Error(`Issue ${ref.issue} is not a feature!`)) }
      }
      if (!ALLOWED_PROJECTS[json.base.repo.full_name].map((x) => { return x[0] }).includes(issue.project.id)) {
        reject(new Error(`Bad project for issue ${ref.issue}.`))
      }
      if ((labels.includes('bug') && !labels.includes('cherry checked')) === true) {
        reject(new Error('Missing cherry check.'))
      }

      resolve(true)
    }).catch((err) => {
      err.response.status === 404
        ? reject(new Error('Issue seems not to exist: ' + err.response.status))
        : reject(new Error('Could not reach Redmine\n' + err.message))
    })
  })
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

            checkIssues(getIssuesFromLogs(logs), labels).catch((err) => { reject(err) })

            resolve(!logs[0].includes('* OTH'))
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

const capitalize = (word) => {
  return word.charAt(0).toUpperCase() + word.slice(1)
}

const print = (res) => {
  const keys = Object.keys(res)
  let reject = false

  keys.forEach((key) => {
    const msg = res[key] === true ? 'Ok   ✔' : `${res[key]}   ✖`
    console.log(`  > ${capitalize(key)}     --> ${msg}`)

    if (res[key] !== true) reject = true
  })

  if (reject) process.exit(1)
}

const main = () => {
  getData().then((json) => {
    process.RAW_JSON = json
    return getLabels(json)
  }).then((labels) => {
    const result = {}
    const arg = process.argv[2]

    if (arg === 'tests') {
      process.exit(1)
    } else {
      if (!labels.includes('bypass tests check')) {
        if (!labels.includes('bypass title check')) {
          result.title = checkTitle(process.RAW_JSON) || true
        }

        if (!labels.includes('bypass content check')) {
          checkContents(process.RAW_JSON, labels)
            .then((res) => {
              result.content = res
              if (res) {
                result.body = checkBody(process.RAW_JSON)

                checkLabels(process.RAW_JSON, labels)
                  .then((data) => {
                    result.labels = data
                    print(result)
                  })
                  .catch((msg) => {
                    result.labels = msg
                    print(result)
                  })
              } else {
                console.log('Ignoring labels and body check as the issue is OTH type.')
                print(result)
              }
            })
            .catch((err) => {
              result.content = err.message
              print(result)
            })
        }
        
      } else {
        console.log('TESTS FORCED.')
      }
    }
    
  }).catch((err) => {
    console.log(err.message)
    process.exit(1)
  })
}

main()
