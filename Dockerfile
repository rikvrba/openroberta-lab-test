FROM openroberta/base-x64

WORKDIR /

RUN echo "START"
RUN ls
RUN mvn clean install 
RUN npm install && npm run build   

RUN ./admin.sh -git-mode create-empty-db
RUN ./ora.sh start-from-git
