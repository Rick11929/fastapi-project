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
                    // 创建并激活虚拟环境
                    bat '''
                        python -m venv venv
                        call venv\Scripts\activate.bat
                        python -m pip install --upgrade pip
                        pip install -r requirements.txt
                        pip install pytest
                    '''
                }
            }
        }
        
        stage('Run Tests') {
            steps {
                script {
                    // 使用虚拟环境运行测试
                    bat '''
                        call venv\Scripts\activate.bat
                        python -m pytest tests/
                    '''
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
                // 清理虚拟环境
                bat '''
                    deactivate || exit 0
                    rmdir /s /q venv || exit 0
                '''
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