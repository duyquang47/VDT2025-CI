pipeline {
  agent {
    kubernetes {
      yamlFile 'kaniko-pod.yaml'
    }
  }

  environment {
    DOCKERHUB_USERNAME = 'quang47'
    DOCKER_IMAGE_NAME = 'examplevotingapp'
    GIT_CONFIG_REPO_CREDENTIALS_ID = 'github'
    GIT_CONFIG_REPO_URL = 'https://github.com/duyquang47/VDT2025-CD.git'
  }

  stages {
    stage('Checkout Source Code') {
      steps {
        echo 'Checking out source code...'
        checkout scm
      }
    }

    stage('Build and Push Images with Kaniko') {
      steps {
        container('kaniko') {
          script {
            def gitCommit = sh(script: 'git rev-parse HEAD', returnStdout: true).trim().substring(0, 8)
            def dockerImageTag = "${DOCKER_IMAGE_NAME}:${gitCommit}"
            def services = ['vote', 'result', 'worker']

            services.each { service ->
              def imageName = "${DOCKERHUB_USERNAME}/examplevotingapp_${service}:${dockerImageTag}"
              def contextDir = "/workspace/app/${service}"

              echo "Building image ${imageName}..."

              sh """
                /kaniko/executor \
                  --dockerfile=${contextDir}/Dockerfile \
                  --context=${contextDir} \
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
        script {
          def gitCommit = sh(script: 'git rev-parse HEAD', returnStdout: true).trim().substring(0, 8)
          def dockerImageTag = "${DOCKER_IMAGE_NAME}:${gitCommit}"
          
          dir('k8s-specifications') {
            echo "Cloning manifest repo..."
            withCredentials([usernamePassword(
              credentialsId: GIT_CONFIG_REPO_CREDENTIALS_ID,
              variable: 'GIT_USER',
              passwordVariable: 'GIT_PASS'
            )]) {
              // Clone repo CD-VDT từ nhánh main vào thư mục cd-vdt-repo
              sh "git clone -b main https://${GIT_USER}:${GIT_PASS}@github.com/quang47/VDT2025-CI.git cd-vdt-repo"
              
              // Di chuyển vào thư mục repo vừa clone
              dir('cd-vdt-repo') {
                echo "Đang cập nhật image tag trong deployment files thành ${dockerImageTag}"
                
                // Cập nhật file deployment.yaml trong thư mục app
                def services = ['vote', 'result', 'worker']
                services.each { service ->
                  def deploymentFile = "k8s-specifications/${service}-deployment.yaml"
                  def imageName = "${DOCKERHUB_USERNAME}/examplevotingapp_${service}:${dockerImageTag}"

                  echo "Updating ${deploymentFile} with image ${imageName}..."
                  sh "sed -i 's|image: .*|image: ${imageName}|g' ${deploymentFile}"
                  sh "git add ${deploymentFile}"
                }
                
                // Cấu hình git user
                sh "git config user.email 'jenkins@example.com'"
                sh "git config user.name 'Jenkins CI'"

                // Thêm file đã sửa đổi vào staging
                sh "git commit -m 'ci: Cập nhật image tag lên ${gitCommit}'"
                // Đẩy thay đổi lên nhánh main của repo
                sh "git push origin main"
              }
            }
          }
        }
      }
    }
  }

  post {
    success {
      echo "Pipeline completed successfully! Build #${env.BUILD_NUMBER}"
      def gitCommit = sh(script: 'git rev-parse HEAD', returnStdout: true).trim().substring(0, 8)
      echo "Git commit: ${gitCommit}"
    }
    failure {
      echo "Pipeline failed! Build #${env.BUILD_NUMBER}"
    }
    always {
      echo 'Pipeline finished.'
      cleanWs()
    }
  }
}