# CI/CD

## Jenkins Pipeline

```groovy
pipeline {
    agent any
    stages {
        stage('Checkout') { steps { checkout scm } }
        stage('Build') { steps { sh 'make build' } }
        stage('Test') { steps { sh 'make test' } }
        stage('Deploy') { steps { sh 'make deploy' } }
    }
    post {
        success { slackSend("✅ Build successful") }
        failure { slackSend("❌ Build failed") }
    }
}
```

## GitLab CI

```yaml
stages:
  - build
  - test
  - deploy

build:
  stage: build
  script:
    - docker build -t $CI_REGISTRY_IMAGE:$CI_COMMIT_SHA .
    - docker push $CI_REGISTRY_IMAGE:$CI_COMMIT_SHA

test:
  stage: test
  script:
    - npm test
    - sonar-scanner

deploy:
  stage: deploy
  script:
    - kubectl set image deployment/web app=$CI_REGISTRY_IMAGE:$CI_COMMIT_SHA
  only:
    - main
```
