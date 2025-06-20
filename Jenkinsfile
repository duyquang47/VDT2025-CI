pipeline {
  agent {
    kubernetes {
      yamlFile 'kaniko-pod.yaml'
    }
  }

  environment {
    DOCKERHUB_USERNAME = 'quang47'
    MANIFEST_REPO_URL = 'https://github.com/duyquang47/VDT2025-CD.git'
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
            def services = ['vote', 'result', 'worker']
            def imageTag = env.BUILD_NUMBER

            services.each { service ->
              def imageName = "${DOCKERHUB_USERNAME}/examplevotingapp_${service}:${imageTag}"
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
          def imageTag = env.BUILD_NUMBER

          dir('manifest-repo') {
            echo "Cloning manifest repo..."
            git url: MANIFEST_REPO_URL, branch: 'main'

            def services = ['vote', 'result', 'worker']
            services.each { service ->
              def deploymentFile = "k8s-specifications/${service}-deployment.yaml"
              def imageName = "${DOCKERHUB_USERNAME}/examplevotingapp_${service}:${imageTag}"

              echo "Updating ${deploymentFile} with image ${imageName}..."
              sh "sed -i 's|image: .*|image: ${imageName}|g' ${deploymentFile}"
            }

            sh 'git config user.name "Jenkins CI"'
            sh 'git config user.email "jenkins@example.com"'
            sh "git commit -am 'Deploy build #${imageTag}'"
            sh 'git push origin main'
          }
        }
      }
    }
  }

  post {
    always {
      echo 'Pipeline finished.'
      cleanWs()
    }
  }
}
