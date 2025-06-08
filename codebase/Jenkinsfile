 
pipeline {

  agent any

  tools {
    
    maven "jenkins-maven"

  }

  stages { 

    stage('TEST'){

      steps {
        sh 'mvn clean install compile test'
      }
     
    }
  }
 
}
