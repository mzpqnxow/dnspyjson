#
# Universal Python deployment and develpment tool Python3 on Linux
# This relies heavily on GNU make
#
# Includes pip, virtualenv, setuptools as well as socks proxy support
# This allows `make boot` to work on any UNIX, Linux or MacOS machine
# regardless of whether it has any of these dependencies installed in
# your local directory or system-wide
#
# MacOS works, with some tweaks (use PYTHON3=/path/to/system/python)
# Also, see the issue with the lack of a `realpath` command (seriously?)
#
#
# Remember that PYTHON3 can be overridden on the command line
# using `make PYTHON3=/opt/my/python`. The same is true of the
# VENV_PATH but there's really no reason to change the venv dir IMO.
#
# TODO(AG): Consider utilizing some of the GNU special PHONY targets
#           to reduce target size and complexity
# Reference: https://www.gnu.org/software/make/manual/html_node/Special-Targets.html
# The following seem likely to be useful:
#   - .ONESHELL
#   - .EXPORT_ALL_VARIABLES
#   - .SILENT
#   - .IGNORE
#		- .DELETE_ON_ERROR
#
# - AG, 2018
#
DEPENDENCIES := date make dirname which uname git rm mv python3 realpath
EPOCH := $(shell date +%s)
DATE_EPOCH = $(shell date +%Y%m%d.%s)
USER_PYPIRC_FILE := ~/.pypirc
ROOT_DIR := $(shell dirname $(realpath $(lastword $(MAKEFILE_LIST))))
PYTHON3 = $(shell which python3)
DOC_MD = README.md
VENV_PATH = venv/
UNAME_S := $(shell uname -s)
PYBUILD := ./pyboot
BUILD_FILES := build dist *.egg-info
PACKAGES := packages
PACKAGES_BIN := $(PACKAGES)/bin
PACKAGES_FULL_PATH := $(ROOT_DIR)/$(PACKAGES)
UPGRADING_TMPDIR := $(ROOT_DIR)/../pyboot.upgrade.inprogress.$(DATE_EPOCH)
BACKUP_RELDIR := pyboot.upgrade.$(EPOCH)
PROJECT_FILES := etc venv $(PACKAGES) pyboot Makefile
PYBOOT_INSTALL_BACKUP_BRNACH := pyboot-install-$(EPOCH)
PYBOOT_BACKUP_BASENAME := pyboot.backup.$(DATE_EPOCH)
PYBOOT_GIT_INITIAL_COMMIT_SCRIPT_NAME := git_init_pyboot.sh
RSYNC_INSTALL_FILE := .rsync_include.lst
# If using make new or make install, use a specific branch, to avoid
# mistakes. Change from master :)
BRANCH = master
GIT_NEW_ADD_FILE := Makefile etc git_init_pyboot.sh packages/ pyboot setup.py venv
PYPIRC := $(ROOT_DIR)/.pypirc.template
# Note, twine is a dependency for publishing to a PyPi instance
TWINE = twine
# Tag the initial checkin when using the `new` target. This makes it
# a step less to utilize versioneer
NEW_REPO_VERSION_TAG = 0.0.1

# These dependencies are to prepare you for building native code Python
# packages. Nothing is required for pyboot to run, except git which is
# required when using the `make new` target!
DEBIAN_DEPS := autoconf automake build-essential git libpython3-dev pandoc python3-dev
# Red Hat package names are not tested, but this should be close ...
# It is possible that python3 and libpython3 headers are just called
# python-devel and libpython-devel *shrug*
REDHAT_DEPS := autoconf automake git python3-devel libpython3-devel
REQUIREMENTS_TXT := $(ROOT_DIR)/venv/requirements.txt
CONSTRAINTS_TXT := $(ROOT_DIR)/venv/constraints.txt
NEW_INSTALL_FILES = .gitignore .pypirc.template
NEW_INSTALL_FILES += setup.py setup.cfg


# If requirements.txt gets hosed, build a new, sane one
define REQUIREMENTS_TXT_CONTENT
# Many of these packages pull in other linters and static analysis tools
# as well, so check venv/bin after you build and see what's there. These
# are mostly small modules and only add 30 seconds or so to your virtual
# environment build time. But you're free to remove them of course
# --- Begin suggested / default venv packages ---
flake8				            # Wraps pyflakes, pycodestyle and mccabe
pylint                          # linters..
pylama                          # linter..
isort                           # cleans up imports, configurable
seed-isort-config               # an isort companion
bandit                          # Static analysis for security issues
pyt                             # Static analysis for security issues, specifically webaoos
pydocstyle                      # Keep you on track with documentation style, per pydoc specs
ipython                         # This will slow your build and bloat your venv, but it's nice to have
setuptools
wheel
yapf
twine                           # The new way to publish to a PyPi repository
# --- End suggested / default venv packages ---

# --- Begin your own requirements ---
endef
export REQUIREMENTS_TXT_CONTENT


define PYBOOT_GIT_INITIAL_COMMIT_SH
#!/bin/bash
git commit -m "Installing pyboot environment"
git push || echo "WARN: Not pushing changes"
git tag 0.0.1  # Recommended starting tag if you plan to use versioneer: 0.0.1
git push --tags
echo "Please consider using versioneer install after updating setup.cfg and setup.py"
echo "With versioneer, you will be able to use 'make release' to autobump tags to"
echo "GitHub, which will allow you to pip install packages by version very easily"
echo "It will also allow you a simple tag-based versioning system to aid in rollbacks"
endef
export PYBOOT_GIT_INITIAL_COMMIT_SH

# If requirements.txt gets hosed, build a new, sane one
define CONSTRAINTS_TXT_CONTENT
endef
export CONSTRAINTS_TXT_CONTENT

define PYPIRC_MESSAGE
-------- Credentialed PyPirc Installation --------

Follow the prompts to install a ~/.pypirc file that allows you to publish to an Artifactory PyPi

WARN: This is a global configuration file for your username
WARN: Any existing ~/.pypirc will be backed up in ~/.pypirc.bak.<timestamp>
-------- PyPirc Crdentials --------

Please enter your credentials and a PyPirc file will be created
SECURITY: The file will be stored mode 0600 in ~/.pypirc, private from other users

endef
export PYPIRC_MESSAGE

define GITIGNORE_MESSAGE
WARN:   At this time, there was no effort to made to keep any special entries in the root
        .gitignore file. You should be OK there since the only files critical for pyboot3
        are subdirectories and innocuous files in root that should never be git ignored;
        These files include:

          - Makefile
		  - pyboot3

        Other files are in subdirectories and include their own directory specific .gitignore
	    files. These include:

          - venv/.gitignore
	      - etc/.gitignore
	      - packages/.gitignore

In summary, installation we complete. Please check for existance of the following:
endef
export GITIGNORE_MESSAGE

define GIT_CONFIG_MESSAGE
You will now have a chance to edit the .git/config file for the project. You may want
to enter a user section for per-project commit identity, or maybe enter other git config
entries. For example, you can set your identity for this specific project like this:

[user]
name = Sam Walton
email = SamTheMan@walmart.com

NOTE: This will not take effect until your first commit!

endef
export GIT_CONFIG_MESSAGE

define PROJECT_HELP_MSG
pyboot3 - https://github.com/mzpqnxow/pyboot3

    Automatically deploy Python Virtual Environments for production applications without any
    system or local user dependencies (i.e. pip, virtualenv, setuptools, pysocks, etc)

    All dependencies to bootstrap a virtualenv are included so there is no need to use
    get-pip.py or to use your system package manager to install pip, virtualenv or any package
    other than Python3 itself. Note you'll need some libraries and headers for certain 3rd
    party packages that utilize native code, e.g. pandas, psycopg2, numpy, ...

    The following summarizes the essential/most useful targets as well as the smaller
    utility targets that most developers will not use often if at all

    Command / Target | Description of Target
                     |
    Essentials       |
    -----------------|----------------------------------------------------------
	make deploy      | Clean existing virtualenv and create new one per venv/ and etc/ settings
	make dev         | Alias for `deploy` (can be customized, see README.md)
	make prod        | Alias for `deploy` (can be customized, see README.md)
	make rebuild     | Alias for `deploy`
	make release*    | Publish a package with version autobump **only when versioneer is properly configured for your project**
	make new**       | Install pyboot3 files into an existing (preferably empty) git project
	=================|==========================================================
    Nice-to-Haves    |
    -----------------|----------------------------------------------------------
    make clean       | Clean the current virtual environment
    make compat      | Same as make test
    make completion  | Add pip table completion to ~/.zshrc and ~/.bashrc files 
    make constraints | Automatically rebuilds constraints file in case of accidental deletion
    make dep         | Attempt to automatically install git, libpython headers, etc. (Optional)
    make doc         | Produce a pretty PDF from a README.md markdown file
    make push        | Perform a simple `git push` command
    make pypirc      | Create a basic ~/.pypirc file from a template, prompting for user/password
    make requirements| Automatically rebuilds requirements files in case of accidental deletion
    make test        | Best-effort check to see if your OS/distro is supported
 
    * When using make release, git version tags are assumed to be of the form x.y.z
        x: Major
        y: Minor
        z: Revision
      Bootstrap this with:
        $ git tag 0.0.1 && git push --tags`
      The following options are available:
    	  - To autobump the revision and push release:
    	    $ make release bump=major
    	  - To autobump the minor and push release:
			    $ make release bump=minor
    	  - To autobump the revision and push release:
    		  $ make release
    	You will most commonly be bumping only the revision

    ** When using `make new`, a repo should be specified:
      $ make new REPO=https://github.com/user/project
      
      There is a risk of files being overwritten if names collide, so it is recommended
      to do this upon initial creation of a project

    Guide to Setting Up a New Project
    ========================

    - Edit venv/requirements-project.txt and commit to set virtual environment dependencies
      that are specific to your project
    - Edit venv/requirements-base.txt and commit to add/remove non-essential but helpful
      packages you may use during development. You will want to comment these packages out
      when deploying to production
    - Edit etc/pip.ini if necessary to customize settings for proxies and internal PyPi
      repositories such as Artifactory
    - (Optional) Use the following command to prepare tag-based versioning if you plan to use versioneer:
        $ git tag 0.0.1 && git push --tags
    - (Optional) Use:
    		$ make dep
    	This will attempt to install dependencies that are common to some 3rd party Python
    	packages using a package manager specific to your OS. Examples include Python3 and
    	libpython3, libyaml shared libraries and headers. Modify if you intend to use it, it
    	is not terribly useful as is, but it provides basic logic to take different actions
    	based on some simple OS/distribution detection
    - Finally, you can build the virtual environment:
    	$ make dev
    	Note the dev, deploy, prod and rebuild targets all perform the same action. It is up
    	to you to modify the makefile
    - Enter the virtual environment in the standard way:
      $ source venv/bin/activate
    ...

endef
export PROJECT_HELP_MSG

K := $(foreach exec,$(DEPENDENCIES),\
        $(if $(shell which $(exec)),some string,$(error "Required app $(exec) not in PATH!")))

all:
	echo "$$PROJECT_HELP_MSG"

requirements: $(REQUIREMENTS_TXT)
constraints: $(CONSTRAINTS_TXT)

deploy: $(VENV_PATH) clean
	echo "Executing pyboot (`basename $(PYBUILD)` -p $(PYTHON3) $(VENV_PATH))"
	$(PYBUILD) -p $(PYTHON3) $(VENV_PATH)

dev: deploy
python3: deploy

$(REQUIREMENTS_TXT): $(VENV_PATH)
	echo "$$REQUIREMENTS_TXT_CONTENT" > $(REQUIREMENTS_TXT)

$(CONSTRAINTS_TXT): $(VENV_PATH)
	echo "$$CONSTRAINTS_TXT_CONTENT" > $(CONSTRAINTS_TXT)

$(VENV_PATH):
	echo 'WARN'; \
	echo 'WARN: VENV_PATH is missing, making directory\nWARN'; \
	mkdir -p $(VENV_PATH)

$(DOC_MD):
	echo You must have a README.md file present or pass DOC_MD=yourdoc.md to make
	/bin/false

# If you have pandoc and supporting packages, make a nice PDF of your documentation
doc: $(DOC_MD)
	pandoc  $(DOC_MD) -o $(DOC_PDF) "-fmarkdown-implicit_figures -o" \
    --from=markdown \
    -V geometry:margin=.4in \
    --toc \
    --highlight-style=espresso

#
# This target is meant for use with versioneer only!!
# To install versioneer, see https://github.com/warner/python-versioneer
# It is very simple to install, use pep440. Once configured, you can
# use this target and greatly simplify publishing to PyPi or Artifactory!!
#
# By default, make release will:
#  - tag your current branch
#      $ make release bump=major
#      $ make release bump=minor
#      $ make release
#  - Publish your Python package to your PyPi repository with the new tag
#  - Perform a git push on any committed changes you have
#  - Perform a git push --tags to add the new tag to git
#
# If you are currently not publishing to a PyPi repository, you
# should comment out the $(TWINE) line. If you *are* publishing, make
# you set up your pypirc (use `make pypirc` to produce a template)
#
release: push
	$(eval v := $(shell git describe --tags --abbrev=0 | sed -Ee 's/^v|-.*//'))
ifeq ($(bump), major)
	$(eval f := 1)
else ifeq ($(bump), minor)
	$(eval f := 2)
else
	$(eval f := 3)
endif
	version=`echo $(v) | awk -F. -v OFS=. -v f=$(f) '{ $$f++ } 1'`
	echo "Pushing tagged release $$version ..."
	git tag -a $$version
	git commit -am "Bumped to version $$version" || /bin/true
	git push --tags
	echo "Release pushed to repository"

push: .FORCE
	echo "Pushing commited changed before tagging release ..."
	git push

publish: release $(PIP_CONF)
ifndef VIRTUAL_ENV
	$(error The publish target is meant only for use in an activated virtual environmnent)
else ifeq (,$(wildcard ./setup.py))
	$(error You must have a setup.py file in the project root if you want to publish)
endif
	echo Building using sdist ..
	$(PYTHON3) setup.py sdist || (rm -rf dist/; echo Failed to build sdist; /bin/false)
	echo Publishing to PyPi using Twine ...
	$(TWINE) upload -r local dist/* --verbose || (rm -rf $(BUILD_FILES); $(error "Twine failed to publish!"))	

freeze: .FORCE
	$(PYBUILD) --freeze $(VENV_PATH)
	echo
	echo
	latest_version=$$(realpath $$(ls -lr $(VENV_PATH)/frozen-requirements-* | tail -1 | awk '{print $$9}'))
	echo You probably want to git add $$latest_version
	echo

pypirc_backup:
ifneq ("$(wildcard ~/.pypirc)", "")
PYPIRC_BACKUP_FILE := "$(shell echo $(USER_PYPIRC_FILE).bak.$(EPOCH))"
endif

pypirc: pypirc_backup
	saved_umask=$(shell umask)
	umask 177
	echo "$$PYPIRC_MESSAGE"
ifdef PYPIRC_BACKUP_FILE
	echo "WARN: You already have a $(USER_PYPIRC_FILE) file present!"
	echo -n "WARN: Press enter and it will be backed up and replaced, control-c to abort.. "
	read decision
	echo "Backing up existing $(USER_PYPIRC_FILE) to "$(PYPIRC_BACKUP_FILE)
	mv $(USER_PYPIRC_FILE) $(PYPIRC_BACKUP_FILE) && rm -f $(USER_PYPIRC_FILE)
endif
	echo "Configuring new $(USER_PYPIRC_FILE):"
	echo "--------------------------"
	echo -n 'Please enter username: '
	read user
	echo -n 'Please enter password (will not be printed to screen): '
	stty -echo
	read pass
	stty echo
	echo
	sed \
    -e "s/%%USER%%/$$user/" \
    -e "s/%%PASS%%/$$pass/" \
    $(PYPIRC) > $(USER_PYPIRC_FILE)
	umask $$saved_umask	
	echo "Installation complete. Please inspect $(USER_PYPIRC_FILE) and modify"
	echo "any necessary settings. Once complete, you may use 'make publish' to"
	echo "publish packages to a PyPi repository using 'twine'"

dep:
ifneq ("$(wildcard /etc/debian_version)", "")
	echo "Debian derivative, using apt to install the following packages:"
	echo "$(DEBIAN_DEPS)"
	sudo apt-get install $(DEBIAN_DEPS)
else ifneq ("$(wildcard /etc/redhat-release)", "")
	echo "Red Hat derivative, using yum to install the following packages:"
	echo "$(REDHAT_DEPS)"
	sudo yum groupinstall "Development Tools"
	sudo yum install $(REDHAT_DEPS)
else ifeq ($(UNAME), Darwin)
	echo "Not familiar with dependency installation process for $(UNAME_S)"
	echo "You probably will need to use brew or some other 3rd party package manager"
else:
	echo "The OS $(UNAME_S) is not known"
	echo "If you have success, please enter a PR with any required changes"
	echo "If you are unable to succeed, please enter an Issue with details"
endif
	exit

# This is hazardous if your project has colliding filenames
# It is meant to be used when your project is empty, right
# after you create the repository!
#
# repo_uri: Full URI for git clone argument with the .git
#                    suffix removed it it was present
#
new: clean
	set -e
	cd $(ROOT_DIR)
	repo_uri=$$(echo $(REPO) | sed -e 's|\.git||')
	repo_name=$$(basename $$repo_uri)
	repo_working_root=$(UPGRADING_TMPDIR)/$$repo_name
	mkdir -p $(UPGRADING_TMPDIR)
	# git clone $$repo_uri --branch $(BRANCH) $(UPGRADING_TMPDIR)/$$repo_name
	git clone $$repo_uri $(UPGRADING_TMPDIR)/$$repo_name
	working_repo_root=$(UPGRADING_TMPDIR)/$$repo_name
	mkdir -p $$working_repo_root/$(PYBOOT_BACKUP_BASENAME)
	rsync -a -P -v --delete-during --backup --backup-dir=$$working_repo_root/$(PYBOOT_BACKUP_BASENAME) --include-from=$(RSYNC_INSTALL_FILE) . $(UPGRADING_TMPDIR)/$$repo_name
	cd $(UPGRADING_TMPDIR)/$$repo_name
	echo "$$GIT_CONFIG_MESSAGE"
	echo -n "Press enter to continue with editing the file with your default editor ($$EDITOR) ... "
	read ok
	$$EDITOR .git/config
	# Used to do this automatically. Now we provide a shellscript in the repo that the user
	# can run to perform these tasks
	# git commit -m "Installing pyboot environment" . || echo "Choosing not to commit, no problem ..."
	# git push || echo "WARN: Not pushing changes"
	# git tag $(NEW_REPO_VERSION_TAG)
	# git push --tags || echo "WARN: Not pushing tags"
	cd $(ROOT_DIR)
	echo "$$PYBOOT_GIT_INITIAL_COMMIT_SH" > $$working_repo_root/$(PYBOOT_GIT_INITIAL_COMMIT_SCRIPT_NAME)
	chmod 755 $$working_repo_root/$(PYBOOT_GIT_INITIAL_COMMIT_SCRIPT_NAME)
	echo ""
	echo "pyboot: Completed, project $$repo_name now has pyboot skeleton checked in !!"
	echo ""
	echo "Use to following to work on your new project:"
	echo ""
	echo "    $ cd $$working_repo_root"
	echo "    $ git log"
	echo "    $ git status"
	echo "    $ git branch -l"
	echo
	echo "NOTICE: If any files were clobbered during upgrade/installation of pyboot3, you can"
	echo "        find backup copies of those files in $$working_repo_root/$(PYBOOT_BACKUP_BASENAME)"
	echo "        in the original file structure, with the original filename and original contents"
	echo "        You should manually and selectively restore them, if needed"
	echo "$$GITIGNORE_MESSAGE"
	echo "$(realpath --relative-to=$PWD $$working_repo_root/$(PYBOOT_BACKUP_BASENAME))"
	echo 
	echo "It is HIGHLY recommended that you review this and then modify it if necessary and then"
	echo "execute it. This will make the changes official in your repository"
	echo
	echo "Thanks, please come again!"

# This target is untested and not very useful. Just do it manually
completion: .FORCE
	pip completion --zsh >> ~/.zshrc
	pip completion --bash >> ~/.bashrc

clean: .FORCE
	set -e
	find $(PACKAGES_FULL_PATH) -name __pycache__ -o -name \*.pyc -exec rm -rf {} \; 2>/dev/null
	find venv -type f -not -name .gitignore -not -name \*constraints\*.txt -not -name \*requirements\*.txt -exec rm -rf {} \;
	find venv -maxdepth 1 -type d -not -name venv -exec rm -rf {} \;
	rm -rf $(BUILD_FILES)

compat: .FORCE
ifeq ($(UNAME_S), Linux)
	echo $(UNAME_S) is well-tested and supported
else ifeq ($(UNAME_S), Darwin)
	echo $(UNAME_S) is supported but untested, please report issues at https://github.com/mzpqnxow/pyboot3/issues
else
	echo $(UNAME_S) is not known to be supported, please report issues at https://github.com/mzpqnxow/pyboot3/issues
endif
	exit

checkmake: .FORCE
	checkmake Makefile

# Rebuild works by just calling deploy because deploy performs a clean
rebuild: deploy

.PHONY: all checkmake clean compat completion constraints dep deploy dev doc freeze publish pypirc rebuild requirements test

.FORCE :

.SILENT : release push publish clean completion checkmake compat dep freeze new pypirc deploy $(DOC_MD) $(REQUIREMENTS_TXT) $(VENV_PATH) $(CONSTRAINTS_TXT)

.ONESHELL : clean new freeze pypirc

.EXPORT_ALL_VARIABLES : new freeze pypirc
