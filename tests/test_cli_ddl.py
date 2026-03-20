"""Testy rozszerzonego CLI z obsługą DDL."""
import pytest
from apex_export_to_md.cli import parse_args, args_to_config
from apex_export_to_md.config import AppConfig


class TestDdlCliArgs:
    def test_default_ddl_enabled(self):
        args = parse_args(["some/dir"])
        config = args_to_config(args)
        assert config.enable_ddl is True
        assert config.enable_html is True

    def test_no_ddl_flag(self):
        args = parse_args(["some/dir", "--no-ddl"])
        config = args_to_config(args)
        assert config.enable_ddl is False

    def test_no_html_flag(self):
        args = parse_args(["some/dir", "--no-html"])
        config = args_to_config(args)
        assert config.enable_html is False

    def test_ddl_files_option(self):
        args = parse_args(["some/dir", "--ddl-files", "a.sql,b.sql"])
        config = args_to_config(args)
        assert config.ddl_files == ["a.sql", "b.sql"]

    def test_html_output_option(self):
        args = parse_args(["some/dir", "--html-output", "docs.html"])
        config = args_to_config(args)
        assert config.html_output == "docs.html"

    def test_author_name_default(self):
        args = parse_args(["some/dir"])
        config = args_to_config(args)
        assert config.author_name == "Tomasz Rembiasz"


class TestAppConfigDefaults:
    def test_new_defaults(self):
        c = AppConfig()
        assert c.enable_ddl is True
        assert c.ddl_files == []
        assert c.enable_html is True
        assert c.html_output == ""
        assert c.author_name == "Tomasz Rembiasz"
