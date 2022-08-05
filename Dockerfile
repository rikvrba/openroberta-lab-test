FROM ubuntu

RUN apt-get update && apt-get -y upgrade && \
    apt-get install -y locales && \
    apt-get install -y tzdata && \
    apt-get install -y git maven && \
    git config --global core.fileMode false && \
    apt-get install -y python-pip && \
    pip install uflash esptool && \
    apt-get update && apt-get -y upgrade && \
    apt-get install -y openjdk-8-jdk && \
    update-java-alternatives -s java-1.8.0-openjdk-amd64 && \
    apt-get install -y wget && \
    apt-get install -y nodejs npm && \
    apt-get clean

RUN git clone https://github.com/rikvrba/openroberta-lab-test.git
RUN cd openroberta-lab-test
RUN ls

RUN mvn clean install 
RUN npm install && npm run build

RUN ./admin.sh -git-mode create-empty-db
RUN ./ora.sh start-from-git
