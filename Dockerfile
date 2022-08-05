FROM openroberta/base-x64:31

RUN curl -sL https://deb.nodesource.com/setup_4.x | bash
# and install node 
RUN apt-get install nodejs
# confirm that it was successful 
RUN node -v
# npm installs automatically 
RUN npm -v

RUN echo "START"
RUN ls
RUN mvn clean install 
RUN npm install && npm run build

RUN ./admin.sh -git-mode create-empty-db
RUN ./ora.sh start-from-git
