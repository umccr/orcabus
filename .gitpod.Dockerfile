FROM --platform=linux/amd64 public.ecr.aws/aws-cli/aws-cli as aws

FROM gitpod/workspace-full

# Our list of tools we need to use for dev (that won't be installed via npm etc)

# python specific version (is incredibly slow to install so we do first to hopefully have this layer cached)
RUN pyenv install 3.10 && pyenv global 3.10

# yarn
RUN curl -sS https://dl.yarnpkg.com/debian/pubkey.gpg | sudo apt-key add -
RUN echo "deb https://dl.yarnpkg.com/debian/ stable main" | sudo tee /etc/apt/sources.list.d/yarn.list
RUN sudo apt-get update && sudo apt-get install -y --no-install-recommends yarn

# nodejs specific version
RUN bash -c 'VERSION="18.19.0" \
    && source $HOME/.nvm/nvm.sh && nvm install $VERSION \
    && nvm use $VERSION && nvm alias default $VERSION'
RUN echo "nvm use default &>/dev/null" >> ~/.bashrc.d/51-nvm-fix

# pre-commit
RUN pip install pre-commit

# aws CLI v2
COPY --from=aws /usr/local/aws-cli/ /usr/local/aws-cli/
COPY --from=aws /usr/local/bin/ /usr/local/bin/
