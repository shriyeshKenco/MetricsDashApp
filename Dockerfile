FROM 823367020558.dkr.ecr.us-east-1.amazonaws.com/kencologistics/codebase@sha256:b6852ea166a1faf055c635c46035b09029eeae3eb2f87c858f0c2c65b9813440


COPY ./requirements.txt /app/requirements.txt
RUN pip install -r /app/requirements.txt
RUN pip install Jinja2==2.11.3 # This will cause a pip conflict with Prefect -- it seems to not cause issue, however.

COPY ./ /app
WORKDIR /app

## Setup prod indicators
ARG PROD_FLAG
ENV DAVINCI_PROD=$PROD_FLAG

# Prod command
CMD ["gunicorn", "app:server", "--workers=3", "--timeout", "1000", "--capture-output", "--bind", "0.0.0.0:80"]