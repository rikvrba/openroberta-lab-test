FROM openroberta/base-x64:31

RUN apt-get update -yq \
    && apt-get install curl gnupg -yq \
    && curl -sL https://deb.nodesource.com/setup_12.x | bash \
    && apt-get install nodejs -yq \
    && npm install html-entities

RUN node -v
# npm installs automatically 
RUN npm -v

RUN echo "START"
RUN ls
RUN mvn clean install 
RUN npm install && npm run build

RUN ./admin.sh -git-mode create-empty-db
RUN ./ora.sh start-from-git
