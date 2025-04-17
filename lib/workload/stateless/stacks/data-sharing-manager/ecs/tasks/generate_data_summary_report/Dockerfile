FROM public.ecr.aws/ubuntu/ubuntu:24.04_stable

ARG TARGETPLATFORM=linux/arm64

ENV VIRTUAL_ENV=/usr/local/uv-venv
ENV LC_ALL=en_US.UTF-8
ENV LANG=en_US.UTF-8
ENV DEBIAN_FRONTEND=noninteractive
## Otherwise timedatectl will get called which leads to 'no systemd' inside Docker
ENV TZ=UTC

RUN \
  apt update -y -q && \
  apt upgrade -y -q && \
  if [ "${TARGETPLATFORM#linux/}" = "" ]; then \
    echo "Could not get platform from '${TARGETPLATFORM}'" 1>&2 && \
    exit; \
  elif [ "${TARGETPLATFORM#linux/}" = "arm64" ]; then \
    platform_url="aarch64";  \
  else \
    platform_url="x86_64"; \
  fi && \
  apt update -yq && \
  apt upgrade -yq && \
  apt install -yq \
    wget \
    jq \
    tar \
    unzip \
    ca-certificates \
    dirmngr \
    ed \
    gpg \
    gpg-agent \
    less \
    locales \
    lsb-release \
    vim-tiny \
    curl && \
  # Install aws cli v2
  wget \
    --quiet \
    --output-document "awscliv2.zip" \
    "https://awscli.amazonaws.com/awscli-exe-linux-${platform_url}.zip" && \
  unzip -q "awscliv2.zip" && \
  ./aws/install && \
  rm "awscliv2.zip" && \
  # Install R through apt
  apt install -y -q \
     r-base \
     r-base-dev \
     r-recommended \
     r-cran-docopt \
     r-cran-tidyverse \
     r-cran-dt \
     r-cran-rmarkdown && \
  # Install the latest version of DT through CRAN \
  Rscript -e "install.packages('DT')" && \
  # Now install python
  curl -LsSf https://astral.sh/uv/install.sh | XDG_CONFIG_HOME=/tmp UV_INSTALL_DIR=/usr/bin sh && \
  rm -rf /tmp/downloaded_packages/ /tmp/*.rds && \
  rm -rf /var/lib/apt/lists/*

COPY docker-entrypoint.sh docker-entrypoint.sh
COPY generate_data_summary_report_template.py generate_data_summary_report_template.py
COPY data_summary_reporting_tools data_summary_reporting_tools

# And now install the required
RUN uv venv && \
  uv pip install data_summary_reporting_tools/.

CMD [ "bash", "docker-entrypoint.sh" ]