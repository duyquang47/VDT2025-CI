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
        sh """
          git clone -b main https://github.com/duyquang47/VDT2025-CI.git /workspace
        """
      }

      // Step 2: Dùng Kaniko build image từ thư mục đã clone
      container('kaniko') {
        script {
          def services = ['vote', 'result', 'worker']

          services.each { service ->
            def imageName = "${DOCKERHUB_USERNAME}/example-voting-app_${service}:${env.GIT_COMMIT_SHORT}"
            def dockerfilePath = "/workspace/app/${service}/Dockerfile"
            def contextPath = "/workspace"

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
        container('git') {
          script {
            dir('k8s-specifications') {
              echo "Cloning manifest repo..."
              withCredentials([usernamePassword(
                credentialsId: GIT_CONFIG_REPO_CREDENTIALS_ID,
                variable: 'GIT_USER',
                passwordVariable: 'GIT_PASS'
              )]) {
                // Clone repo CD-VDT từ nhánh main vào thư mục cd-vdt-repo
                sh "git clone -b main https://${GIT_USER}:${GIT_PASS}@github.com/quang47/VDT2025-CD.git cd-vdt-repo"
                
                // Di chuyển vào thư mục repo vừa clone
                dir('cd-vdt-repo') {
                  echo "Đang cập nhật image tag trong deployment files thành ${env.GIT_COMMIT_SHORT}"
                  
                  // Cập nhật file deployment.yaml trong thư mục app
                  def services = ['vote', 'result', 'worker']
                  services.each { service ->
                    def deploymentFile = "k8s-specifications/${service}-deployment.yaml"
                    def imageName = "${DOCKERHUB_USERNAME}/example-voting-app_${service}:${env.GIT_COMMIT_SHORT}"

                    echo "Updating ${deploymentFile} with image ${imageName}..."
                    sh "sed -i 's|image: .*|image: ${imageName}|g' ${deploymentFile}"
                    sh "git add ${deploymentFile}"
                  }
                  
                  // Cấu hình git user
                  sh "git config user.email 'jenkins@example.com'"
                  sh "git config user.name 'Jenkins CI'"

                  // Thêm file đã sửa đổi vào staging
                  sh "git commit -m 'ci: Cập nhật image tag lên ${env.GIT_COMMIT_SHORT}'"
                  // Đẩy thay đổi lên nhánh main của repo
                  sh "git push origin main"
                }
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
      echo "Git commit: ${env.GIT_COMMIT_SHORT}"
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