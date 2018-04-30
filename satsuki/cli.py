# -*- coding: utf-8 -*-
"""satsuki cli."""
import os
import platform
import sys

import click

import satsuki

click.disable_unicode_literals_warning = True

@click.command(context_settings=dict(
    ignore_unknown_options=True,
))
@click.version_option(version=satsuki.__version__)
@click.option('--token', 'token', envvar='SATS_TOKEN',
    default=None, help='[Required] The OATH GitHub API token to use'
    + 'to connect.')  
@click.option('--command', '-c', 'command', envvar='SATS_COMMAND', 
    type=click.Choice([
        satsuki.Arguments.COMMAND_DELETE, 
        satsuki.Arguments.COMMAND_UPSERT
    ]), default=satsuki.Arguments.COMMAND_UPSERT,
    help='Command to create/update a release.')        
@click.option('--repo', '-r', 'repo', envvar='SATS_REPO',
    default=None, help='[Required] Either the tag name OR the '
    + '--latest option must be provided. If both are used, tag name '
    + 'takes precedence.')    
@click.option('--user', '-u', 'user', envvar='SATS_USER',
    default=None, help='[Required] Either the tag name OR the '
    + '--latest option must be provided. If both are used, tag name '
    + 'takes precedence.')             
@click.option('--tag-name', '-t', 'tag_name', envvar='SATS_TAG_NAME',
    default=None, help='[Required] Either the tag name OR the '
    + '--latest option must be provided. If both are used, tag name '
    + 'takes precedence.')  
@click.option('--rel-name', '-r', 'rel_name', envvar='SATS_REL_NAME',
    default=None, help='The name of the release. Default: tag name')  
@click.option('--latest', 'latest', is_flag=True, default=False,
    help='[Required][Flag] Either this option OR --tag-name must be '
    + 'used. When used, Satsuki will perform any operations on the '
    + 'latest release. Default: Not')     
@click.option('--body', '-b', 'body', envvar='SATS_BODY',
    default=None, help='The blurb that shows up with releases. '
    + 'Default: None')  
@click.option('--commitish', '-o', 'commitish', envvar='SATS_COMMITISH',
    default=None, help='Specifies the commitish value that determines '
    + 'where the Git tag is created from. Default: None')  
@click.option('--file', '-f', 'file', envvar='SATS_FILE', multiple=True,
    default=[], help='File(s) to be uploaded as release asset(s). '
    + 'If the file name contains an asterik (*) it will be treated as '
    + 'a POSIX-style glob and all matching files will be uploaded. ' 
    + 'This option can be used multiple times to upload multiple '
    + 'files. Default: No file is uploaded.')  
@click.option('--label', '-l', 'label', envvar='SATS_LABEL',
    default=None, help='Label to display for files instead of the '
    + 'file name. Not recommended with multiple file upload since '
    + 'all will share the same lable. Default: GitHub will use the '
    + 'raw file name.')  
@click.option('--mime', '-m', 'mime', envvar='SATS_MIME',
    default=None, help='The mime type for files. Default: A guess of '
    + 'the file type or ``application/octet-stream`` if all else '
    + 'fails.')  
@click.option('--pre', '-p', 'pre', envvar='SATS_PRERELEASE', 
    is_flag=True, default=False, help='[Flag] Whether or not this '
    + 'release is a prerelease. Default: Not')  
@click.option('--draft', '-d', 'draft', envvar='SATS_DRAFT', 
    is_flag=True, default=False, help='[Flag] Whether or not this '
    + 'release is a draft. Default: Not')        
@click.option('--verbose', '-v', 'verbose', envvar='SATS_VERBOSE',
    is_flag=True, default=None, help='Verbose mode')     

def main(**kwargs):
    """Entry point for Satsuki CLI."""

    print("Satsuki CLI,", satsuki.__version__)

    # Create an instance
    args = satsuki.Arguments(**kwargs)
    rm = satsuki.ReleaseMgr(args=args)
    #sys.exit(rm.execute())