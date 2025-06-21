pipeline {
  agent {
    kubernetes {
      yamlFile 'kaniko-pod.yaml'
    }
  }

  environment {
    DOCKERHUB_USERNAME = 'quang47'
    GIT_CONFIG_REPO_CREDENTIALS_ID = 'github'
    GIT_CONFIG_REPO_URL = 'https://github.com/duyquang47/VDT2025-CD.git'
  }

  stages {
    stage('Checkout Source Code') {
      steps {
        checkout scm
      }
    }

    stage('Get Git Commit') {
      steps {
        container('git') {
          script {
            def workspacePath = sh(script: 'pwd', returnStdout: true).trim()
            echo "Current workspace: ${workspacePath}"
            
            sh "git config --global --add safe.directory '${workspacePath}'"
            sh 'git config --global user.email "jenkins@example.com"'
            sh 'git config --global user.name "Jenkins CI"'          
            sh 'git config --global safe.directory "*"'
            
            env.GIT_COMMIT_SHORT = sh(script: 'git rev-parse HEAD', returnStdout: true).trim().substring(0, 8)
            echo "Git commit: ${env.GIT_COMMIT_SHORT}"
          }
        }
      }
    }

    stage('Build and Push Images with Kaniko') {
      steps {

        container('kaniko') {
          script {
            // def services = ['vote', 'result', 'worker']
            def services = ['vote']

            services.each { service ->
              def imageName = "${DOCKERHUB_USERNAME}/example-voting-app_${service}:${env.GIT_COMMIT_SHORT}"
              sh """
                /kaniko/executor \
                  --dockerfile=/workspace/app/${service}/Dockerfile \
                  --context=/workspace \
                  --destination=${imageName}
              """
            }
          }
        }
      }
    }

    stage('Update K8s Manifests') {
      steps {
        script {
          echo "Cloning manifest repo..."
          withCredentials([usernamePassword(
            credentialsId: GIT_CONFIG_REPO_CREDENTIALS_ID,
            usernameVariable: 'GIT_USER',
            passwordVariable: 'GIT_PASS'
          )]) {
            sh "git clone -b main https://${GIT_USER}:${GIT_PASS}@github.com/duyquang47/VDT2025-CD.git config-repo"

            dir('config-repo') {
              echo "Đang cập nhật image tag..."

              // def services = ['vote', 'result', 'worker']
              def services = ['vote']
              
              services.each { service ->
                def valueFile = "helm/values.yaml"
                def imageName = "${DOCKERHUB_USERNAME}/example-voting-app_${service}:${env.GIT_COMMIT_SHORT}"

                echo "Updating ${service} with image ${imageName}..."

                def imageTag = "${env.GIT_COMMIT_SHORT}"

                sh "sed -i 's|^vote-image:.*|vote-image: ${imageName}|' ${valueFile}"
                sh "sed -i 's|^vote-tag:.*|vote-tag: ${imageTag}|' ${valueFile}"

                sh "git add ${valueFile}"
              }

              sh "git config user.email 'jenkins@example.com'"
              sh "git config user.name 'Jenkins CI'"
              sh "git diff --quiet || git commit -m 'ci: Cập nhật image tag lên ${env.GIT_COMMIT_SHORT}'"
              sh "git push https://${GIT_USER}:${GIT_PASS}@github.com/duyquang47/VDT2025-CD.git HEAD:main"
            }
          }
        }
      }
    }
  }

  post {
    success {
      echo "Pipeline completed successfully! Build #${env.BUILD_NUMBER}"
      echo "Git commit: ${env.GIT_COMMIT_SHORT}"
    }
    failure {
      echo "Pipeline failed! Build #${env.BUILD_NUMBER}"
    }
    always {
      echo 'Clean workspaces.'
      cleanWs()
    }
  }
}
