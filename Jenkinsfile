pipeline {
    agent any
    
    environment {
        DOCKER_IMAGE = 'fastapi-app'
        DOCKER_TAG = 'latest'
    }
    
    stages {
        stage('Checkout') {
            steps {
                checkout scm
            }
        }
        
        stage('Setup Python Environment') {
            steps {
                script {
                    // 分步执行命令以便于调试
                    bat 'python -m venv venv'
                    bat 'venv\Scripts\activate.bat && python -m pip install --upgrade pip'
                    bat 'venv\Scripts\activate.bat && pip install -r requirements.txt'
                    bat 'venv\Scripts\activate.bat && pip install pytest'
                }
            }
        }
        
        stage('Run Tests') {
            steps {
                script {
                    bat 'venv\Scripts\activate.bat && python -m pytest tests/'
                }
            }
        }
        
        stage('Build Docker Image') {
            steps {
                script {
                    bat 'docker build -t %DOCKER_IMAGE%:%DOCKER_TAG% .'
                }
            }
        }
        
        stage('Stop Old Container') {
            steps {
                script {
                    bat 'docker-compose down || exit 0'
                }
            }
        }
        
        stage('Deploy') {
            steps {
                script {
                    bat 'docker-compose up -d'
                }
            }
        }
    }
    
    post {
        always {
            script {
                bat 'venv\Scripts\deactivate.bat || exit 0'
                bat 'rmdir /s /q venv || exit 0'
                cleanWs()
            }
        }
        success {
            echo '部署成功！'
        }
        failure {
            echo '部署失败，请检查日志！'
        }
    }
}