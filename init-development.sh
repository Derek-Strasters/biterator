#!/usr/bin/env bash

### Set up the development environment.

set -vxe



## If Mac-OS:
if [[ $OSTYPE == 'darwin'* ]]; then
	## Install Prerequisites.
	brew install openssl readline sqlite3 xz zlib

	## Install pyenv (python version manager).
	curl https://pyenv.run | bash

	# Restart shell.
	reset

	# Reload shell start scripts.
	set +vx
	source "$HOME"/.bash_profile
	set -vx

	# Update pyenv
	pyenv update

	# Install project specific python verison
	pyenv install "$(<.python-version)"


## If Ubuntu:
elif [[ $OSTYPE == "linux-gnu"* ]]; then
	## Install Prerequisites.
	sudo apt-get update;
	sudo apt-get install make build-essential libssl-dev zlib1g-dev \
			 libbz2-dev libreadline-dev libsqlite3-dev wget curl llvm \
			 libncursesw5-dev xz-utils tk-dev libxml2-dev libxmlsec1-dev libffi-dev liblzma-dev


	## Install pyenv (python version manager).
	curl https://pyenv.run | bash

	# Restart shell.
	reset

	# Reload shell start scripts.
	set +vx
	source "$HOME"/.profile
	set -vx

	# Update pyenv.
	pyenv update

	# Install project specific python version.
	pyenv install "$(<.python-version)"


## If git-bash Windows.
elif [[ $OSTYPE == "msys"* ]]; then

	if [[ ! -d "$HOME/.pyenv" ]]; then
		## Install pyenv (python version manager).
		git clone https://github.com/pyenv-win/pyenv-win.git "$HOME/.pyenv"
	fi

	# NOTE: If you are running Windows 10 1905 or newer, you might need to disable the built-in Python launcher via
	# Start > "Manage App Execution Aliases" and turning off the "App Installer" aliases for Python

	# If pyenv is not in the windows path and env vars:
	if [[ -z $(printenv PYENV) ]]; then

		# Add pyenv path stuff to environmental variables.
		powershell.exe <<-'EOF'
			[System.Environment]::SetEnvironmentVariable('PYENV',$env:USERPROFILE + "\.pyenv\pyenv-win\","Machine")
			[System.Environment]::SetEnvironmentVariable('PYENV_ROOT',$env:USERPROFILE + "\.pyenv\pyenv-win\","Machine")
			[System.Environment]::SetEnvironmentVariable('PYENV_HOME',$env:USERPROFILE + "\.pyenv\pyenv-win\","Machine")
			[System.Environment]::SetEnvironmentVariable('path', $env:USERPROFILE + "\.pyenv\pyenv-win\bin;" + $env:USERPROFILE + "\.pyenv\pyenv-win\shims;" + [System.Environment]::GetEnvironmentVariable('path', "User"),"User")
			EOF

		# Restart shell.
		reset

		# Reload shell start scripts.
		set +vx
		source "$HOME"/.bash_profile
		set -vx

	fi

	# Stop if this causes an error.
	pyenv --version
	# If you receive a "command not found" error, ensure all environment variables are properly set via the GUI:
	# This PC → Properties → Advanced system settings → Advanced → Environment Variables... → PATH

	# Restart shell.
	reset

	# Reload shell start scripts.
	set +vx
	source "$HOME"/.bash_profile
	set -vx

	# Update pyenv
	pyenv update

	# Rebuild shims for pyenv
	pushd "$HOME"
	pyenv rehash
	popd

	# Install project specific python version.
	pyenv install -q "$(<.python-version)"
fi

## OS independent
## Install poetry
curl -sSL https://raw.githubusercontent.com/python-poetry/poetry/master/install-poetry.py | python -

## If Mac-OS or Ubuntu:
if [[ $OSTYPE == 'darwin'* || $OSTYPE == "linux-gnu"* ]]; then
	poetry completions bash > /etc/bash_completion.d/poetry.bash-completion
fi

# More reset
reset

## If Mac-OS or Windows git-bash
if [[ $OSTYPE == 'darwin'* || $OSTYPE == "msys"* ]]; then
	# Reload shell start scripts.
	set +vx
	source "$HOME"/.bash_profile
	set -vx

## If Ubuntu:
elif [[ $OSTYPE == "linux-gnu"* ]]; then
	# Reload shell start scripts.
	set +vx
	source "$HOME"/.profile
	set -vx
fi

# Install dependencies
poetry install

# Activate Git Hooks
poetry run pre-commit install

# Finish
echo "If you cannot read this message, your setup has failed."