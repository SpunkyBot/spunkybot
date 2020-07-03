# This Makefile is part of spunkybot, a multi-platform administration and RCON tool for Urban Terror
# License: MIT

NAME = spunkybot

# Folder structure
BIN_DIR = /opt/$(NAME)
CONF_DIR = $(BIN_DIR)/conf
LIB_DIR = $(BIN_DIR)/lib

# Find suitable Python version (need Python 2.x):
PYTHON ?= $(shell (python -c 'import sys; sys.exit(int(not(sys.version_info.major == 2)));' && which python) \
               || (python2 -c 'import sys; sys.exit(int(not(sys.version_info.major == 2)));' && which python2))
ifeq ($(PYTHON),)
  $(error No suitable Python2 found)
endif

# Fetch version from project
VERSION := $(shell $(PYTHON) setup.py --version)

# Get the branch information from git
ifneq ($(shell which git),)
  GIT_HASH := $(shell git rev-parse --short HEAD)
  GIT_BRANCH := $(shell git rev-parse --abbrev-ref HEAD)
  GIT_INFO = $(GIT_BRANCH)-$(GIT_HASH)
else
  GIT_BRANCH = "develop"
  GIT_INFO = $(GIT_BRANCH)
endif

all:
	@echo "Run 'sudo make install && sudo make config' for installation or 'make help' for a list of all options"

help:
	@echo "make install:         Install $(NAME)"
	@echo "make config:          Install start scripts"
	@echo "make init:            Install all build requirements"
	@echo "make sdist:           Create a source distribution"
	@echo "make clean:           Remove the compiled files (*.pyc, *.pyo)"
	@echo "make dist:            Create a distribution tar file"
	@echo "make snapshot:        Create a zip and tar file of the current git revision"
	@echo "make version:         Show version of $(NAME)"
	@echo "make todo:            Look for TODO markers in the source code"
	@echo "make uninstall:       Un-install $(NAME) and remove all related files"

clean:
	@echo "Cleaning up distutils stuff"
	@-rm -rf build dist .egg *.egg-info
	@echo "Cleaning up byte compiled python stuff"
	@find . -type f -name "*.pyc" -delete
	@find . -type f -name "*.pyo" -delete
	@find . -type d -name "__pycache__" -delete
	@find . -type f -name "*.log*" -delete

install:
	install -d $(DESTDIR)$(BIN_DIR)
	install -d $(DESTDIR)$(CONF_DIR)
	install -d $(DESTDIR)$(LIB_DIR)
	install -m 755 spunky.py $(DESTDIR)$(BIN_DIR)
	install -m 644 README.md LICENSE $(DESTDIR)$(BIN_DIR)
	install -m 644 conf/* -t $(DESTDIR)$(CONF_DIR)
	install -m 644 lib/* -t $(DESTDIR)$(LIB_DIR)

config:
	install -m 755 debian-startscript /etc/init.d/spunkybot
	install -m 755 systemd-spunkybot.service /lib/systemd/system/spunkybot.service

distclean: clean

uninstall:
	-rm -rf $(DESTDIR)$(BIN_DIR)

init:
	if [ -f requirements.txt ]; then pip install -r requirements.txt; fi

version:
	@echo $(VERSION)

dist:
	@tar -czf $(NAME)-$(VERSION).tar.gz --exclude-vcs --exclude-backups --exclude="lib/*.pyc" spunky.py README.md LICENSE setup.py Makefile systemd-spunkybot.service debian-startscript conf/*.conf lib/ doc/Commands.md doc/commands.html --owner=root --group=root --transform="s,^,$(NAME)-$(VERSION)/,S"

sdist_check:
	$(PYTHON) -c 'import setuptools, sys; sys.exit(int(not(tuple(map(int, setuptools.__version__.split("."))) > (18, 5, 0))))'

sdist: sdist_check clean
	$(PYTHON) setup.py sdist

snapshot:
	git archive --prefix='$(NAME)-$(GIT_BRANCH)/' --format=zip HEAD > $(NAME)-$(GIT_INFO).zip
	git archive --prefix='$(NAME)-$(GIT_BRANCH)/' --format=tar HEAD | gzip > $(NAME)-$(GIT_INFO).tar.gz

todo:
	@grep --color -Ion '\(TODO\|todo\).*' -r spunky.py

.PHONY: all clean install config dist sdist sdist_check distclean uninstall init version help snapshot todo
