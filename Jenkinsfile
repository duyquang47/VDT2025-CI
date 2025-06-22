pipeline {
  agent {
    kubernetes {
      yamlFile 'kaniko-pod.yaml'
    }
  }

  environment {
    DOCKERHUB_USERNAME = 'quang47'
    GIT_CONFIG_REPO_CREDENTIALS_ID = 'github-cd'
    GIT_CONFIG_REPO_URL = 'https://github.com/duyquang47/VDT2025-CD.git'
  }

  stages {
    stage('Checkout Source Code') {
      steps {
        echo 'Checking out source code...'
        checkout scm
      }
    }

    stage('Get Git Commit') {
      steps {
        container('git') {
          script {
            // Get the current workspace path
            def workspacePath = sh(script: 'pwd', returnStdout: true).trim()
            echo "Current workspace: ${workspacePath}"
            
            // Configure git to handle ownership issues
            sh "git config --global --add safe.directory '${workspacePath}'"
            sh 'git config --global user.email "jenkins@example.com"'
            sh 'git config --global user.name "Jenkins CI"'
            
            // Alternative: disable ownership check
            sh 'git config --global safe.directory "*"'
            
            env.GIT_COMMIT_SHORT = sh(script: 'git rev-parse HEAD', returnStdout: true).trim().substring(0, 8)
            echo "Git commit: ${env.GIT_COMMIT_SHORT}"
          }
        }
      }
    }

    stage('Build and Push Images with Kaniko') {
      steps {
        // Step 1: Clone Git repo trước
        container('git') {
          sh "git clone -b main https://github.com/duyquang47/VDT2025-CI.git /workspace/source-repo"
        }

        // Step 2: Dùng Kaniko build image từ thư mục đã clone
        container('kaniko') {
          script {
            // def services = ['vote', 'result', 'worker']
            def services = ['vote']

            services.each { service ->
              def imageName = "${DOCKERHUB_USERNAME}/example-voting-app_${service}:${env.GIT_COMMIT_SHORT}"
              def dockerfilePath = "/workspace/source-repo/app/${service}/Dockerfile"
              def contextPath = "/workspace/source-repo/app/${service}"

              echo "Building image ${imageName} from ${dockerfilePath}"

              sh """
                /kaniko/executor \
                  --dockerfile=${dockerfilePath} \
                  --context=${contextPath} \
                  --destination=${imageName} \
                  --verbosity=info
              """
            }
          }
        }
      }
    }

  stage('Update K8s Manifests') {
    steps {
      // BƯỚC 1: DÙNG CONTAINER 'git' ĐỂ CLONE REPO
      container('git') {
        script {
            echo "Cloning manifest repo..."
            withCredentials([usernamePassword(
                credentialsId: GIT_CONFIG_REPO_CREDENTIALS_ID,
                usernameVariable: 'GIT_USER',
                passwordVariable: 'GIT_PASS'
            )]) {
              sh "git clone -b main ${GIT_CONFIG_REPO_URL} /workspace/config-repo"
            }
          }
        }

      // BƯỚC 2: DÙNG CONTAINER 'yq' ĐỂ SỬA FILE YAML
      container('yq') {
        script {
          dir('/workspace/config-repo') {
            echo "Updating helm/values.yaml with yq..."
            def services = ['vote', 'result']
            def valueFile = "helm/values.yaml"

            services.each { service ->
              def imageNameOnly = "${DOCKERHUB_USERNAME}/example-voting-app_${service}"
              def imageTag = env.GIT_COMMIT_SHORT
              
              echo "Updating ${service} -> image: ${imageNameOnly}, tag: ${imageTag}"
              
              // Lệnh yq giờ sẽ chạy trong container 'yq'
              sh "yq e -i '.${service}.image = \"${imageNameOnly}\"' ${valueFile}"
              sh "yq e -i '.${service}.tag = \"${imageTag}\"' ${valueFile}"
            }
          }
        }
      }
          
      // BƯỚC 3: DÙNG LẠI CONTAINER 'git' ĐỂ COMMIT VÀ PUSH
      container('git') {
        script {
          dir('/workspace/config-repo') {
            echo "Committing and pushing changes..."
            sh "git config user.email 'jenkins-ci-bot@example.com'"
            sh "git config user.name 'Jenkins CI Bot'"
            sh """
            if ! git diff --quiet helm/values.yaml; then
                git add helm/values.yaml
                git commit -m "CI: Update image tags to ${env.GIT_COMMIT_SHORT}"
                git push https://${GIT_USER}:${GIT_PASS}@github.com/duyquang47/VDT2025-CD.git HEAD:main
            else
                echo "No changes detected. Skipping commit."
            fi
            """
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