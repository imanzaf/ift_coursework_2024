FROM python:3.10-bullseye

RUN apt-get update && \
        apt-get -y install -y \
        openjdk-11-jdk 

# Install dependencies for Chrome & ChromeDriver
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    wget unzip ca-certificates \
    libnss3 libatk-bridge2.0-0 libgtk-3-0 libgbm1 xvfb && \
    rm -rf /var/lib/apt/lists/*

# Download & install Chrome 133.0.6943.141 from "chrome-for-testing-public"
RUN mkdir -p /opt/chrome && \
    wget -q -O /tmp/chrome.zip \
      "https://storage.googleapis.com/chrome-for-testing-public/133.0.6943.141/linux64/chrome-linux64.zip" && \
    unzip /tmp/chrome.zip -d /opt/chrome/ && \
    rm /tmp/chrome.zip && \
    # Symlink Chrome binary to /usr/bin/google-chrome so Selenium can find it
    ln -s /opt/chrome/chrome-linux64/chrome /usr/bin/google-chrome

# Download & install matching ChromeDriver 133.0.6943.141
RUN wget -q -O /tmp/chromedriver.zip \
      "https://storage.googleapis.com/chrome-for-testing-public/133.0.6943.141/linux64/chromedriver-linux64.zip" \
    && unzip /tmp/chromedriver.zip -d /tmp \
    && mv /tmp/chromedriver-linux64/chromedriver /usr/bin/chromedriver \
    && chmod +x /usr/bin/chromedriver \
    && rm -rf /tmp/chromedriver.zip /tmp/chromedriver-linux64

# (Optional) Verify versions
RUN google-chrome --version || echo "Chrome not found" && \
    chromedriver --version || echo "ChromeDriver not found"

# get jenkins
RUN set -eux; \
        mkdir /home/jenkins/; \
        wget -O /home/jenkins/jenkins.jar https://get.jenkins.io/war-stable/2.414.3/jenkins.war; \
        chmod -R 770 /home/jenkins

# Set environment variables
ENV PATH $PATH:$SPARK_HOME/bin
ENV PYTHONPATH $SPARK_HOME/python:$PYTHONPATH
ENV PYSPARK_PYTHON python

# Install necessary R packages (replace these with your required packages)
# move jenkins configurations
COPY --chmod=770 --from=assets_jenkins . /home/.jenkins/

# install all R packages
# RUN R -e 'packToInst <- read.csv("/opt/apps/batched/R/requirements.txt"); lapply(packToInst$Packages, function(x) install.packages(x))'
RUN python -m pip install poetry
CMD pip3 -v
