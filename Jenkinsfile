// Jenkinsfile
pipeline {
    agent any

    environment {
        // Thay thế bằng username Docker Hub của bạn
        DOCKERHUB_USERNAME = 'quang47'
        // ID của credentials đã lưu trong Jenkins
        REGISTRY_CREDENTIALS = 'docker'
        // URL của repo chứa manifest (thay thế bằng repo của bạn)
        MANIFEST_REPO_URL = 'https://github.com/duyquang47/VDT2025-CD.git'
    }

    stages {
        stage('Checkout Source Code') {
            steps {
                echo 'Checking out application source code...'
                checkout scm
            }
        }

        stage('Build and Push Images') {
            steps {
                script {
                    // Mảng chứa tên các service cần build
                    def services = ['vote', 'result', 'worker']
                    
                    withDockerRegistry(credentialsId: REGISTRY_CREDENTIALS, url: 'https://index.docker.io/v1/') {
                        services.each { service ->
                            // Tên image trên Docker Hub
                            def imageName = "${DOCKERHUB_USERNAME}/examplevotingapp_${service}"
                            // Tag image bằng số thứ tự build của Jenkins
                            def imageTag = "${env.BUILD_NUMBER}"
                            def fullImageName = "${imageName}:${imageTag}"
                            
                            echo "Building and pushing image for ${service}..."
                            
                            // Build image từ Dockerfile trong thư mục của service
                            def dockerImage = docker.build(fullImageName, "./app/${service}")
                            
                            // Push image lên Docker Hub
                            dockerImage.push()
                            
                            echo "Successfully pushed ${fullImageName}"
                        }
                    }
                }
            }
        }

        stage('Update K8s Manifests') {
            steps {
                script {
                    def imageTag = env.BUILD_NUMBER
                    
                    // Tạo một thư mục riêng để checkout manifest repo
                    dir('manifest-repo') {
                        echo "Checking out manifest repository..."
                        git url: MANIFEST_REPO_URL, branch: 'main'

                        def services = ['vote', 'result', 'worker']
                        services.each { service ->
                            def deploymentFile = "k8s-specifications/${service}-deployment.yaml"
                            def imageName = "${DOCKERHUB_USERNAME}/examplevotingapp_${service}"
                            
                            echo "Updating deployment file: ${deploymentFile} with image tag: ${imageTag}"

                            // Dùng `sed` để thay thế image tag trong file deployment
                            sh "sed -i 's|image: .*|image: ${imageName}:${imageTag}|g' ${deploymentFile}"
                        }
                        
                        echo "Committing and pushing manifest changes..."
                        // Cấu hình git user để commit
                        sh 'git config user.email "jenkins@example.com"'
                        sh 'git config user.name "Jenkins CI"'
                        
                        sh 'git add .'
                        sh "git commit -m 'Deploy build #${env.BUILD_NUMBER}'"
                        sh 'git push origin main'
                    }
                }
            }
        }
    }
    
    post {
        always {
            echo 'CI/CD pipeline finished.'
            // Dọn dẹp workspace
            cleanWs()
        }
    }
}