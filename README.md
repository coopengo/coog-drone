# Drone
## Install drone server
1. First install [`docker`](https://docs.docker.com/get-started/) and [`docker-compose`](https://docs.docker.com/compose/gettingstarted/) on your server.
2. Move this `drone` directory anywhere on your server.
3. Build the image needed to run tests:
```
/path/to/drone/images/base/build.sh
```
4. [Make your application recognized by Github so you can have Github tokens.](https://github.com/settings/applications/new)
5. Then export the following variables (put them into the /.bashrc file might be wise enough):
```
export TEST_DRONE_GITHUB_CLIENT=SDFGHJK2345678
export TEST_DRONE_GITHUB_SECRET=EDFGHJ456789HGVJK
export TEST_DRONE_SECRET=anyStringYouWant
```
6. Set `DRONE_HOST` in the `docker-compose.yml` file to your server adress.
7. Run `cd path/to/drone/server && docker-compose up -d`
8. All clear! Now you can do the `Configuration part`.

## Configuration
You will need to configure global secrets for your server to be able to access redmine and github.
1. __(Optional)__ Enter for the REDMINE_TOKEN and GITHUB_TOKEN with the following names:
```
export TEST_REDMINE_TOKEN=DFGHKJLJLHGFDY
export TEST_GITHUB_TOKEN=RTDYFUIYUOIOUTIR567
```
2. Go to the url of your drone server and log in.
3. Go to the `account` part and switch on the repository you want to enable CI on.
4. Go to the `dashboard` of that directory and click on `Secrets`.
5. Add the following secrets with the according values:
  * `GITHUB_TOKEN`
  * `REDMINE_TOKEN`
6. All clear!
