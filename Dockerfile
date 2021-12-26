FROM debian:latest
RUN apt update && apt install -y python3 python3-pip git
RUN pip3 install webdavclient3 
RUN git clone https://github.com/CubicrootXYZ/Mail-to-Cloud.git /opt/app

#RUN mkdir /opt/app
#RUN mv /tmp/app/* /opt/app
#RUN rm -rf /tmp
RUN mkdir -p /opt/app/attachments
CMD [ "python3", "-u", "/opt/app/run.py"]
