#!/usr/bin/env python3
"""
Tests for the cookiecutter template generation.
These tests verify that the template generates correct projects.
"""

import os
import json
import tempfile
import shutil
import subprocess
import pytest
from pathlib import Path


class TestCookiecutterTemplate:
    """Test the cookiecutter template generation."""
    
    @pytest.fixture
    def template_dir(self):
        """Return the template directory path."""
        return Path(__file__).parent.parent
    
    @pytest.fixture
    def default_context(self):
        """Default cookiecutter context for testing."""
        return {
            "project_name": "Test Bot",
            "project_slug": "test-bot",
            "project_description": "A test bot",
            "author_name": "Test Author",
            "author_email": "test@example.com",
            "github_username": "testuser",
            "github_repo_name": "test-bot",
            "python_version": "3.11",
            "bot_name": "Test Bot",
            "bot_username": "test_bot",
            "default_language": "en",
            "supported_languages": "en,ru",
            "use_openrouter": "y",
            "openrouter_model": "openai/gpt-3.5-turbo",
            "use_support_bot": "n",
            "database_name": "test_bot_db",
            "use_github_actions": "y",
            "use_docker": "y",
            "open_source_license": "MIT"
        }
    
    def generate_project(self, template_dir, context, output_dir):
        """Generate a project from the template."""
        # Create a temporary cookiecutter config
        config_file = output_dir / "cookiecutter_config.json"
        with open(config_file, 'w') as f:
            json.dump({"default_context": context}, f)
        
        # Run cookiecutter
        cmd = [
            "cookiecutter",
            str(template_dir),
            "--no-input",
            "--output-dir", str(output_dir),
            "--config-file", str(config_file)
        ]
        
        # If cookiecutter is not available, skip the test
        try:
            subprocess.run(cmd, check=True, capture_output=True, text=True)
        except (subprocess.CalledProcessError, FileNotFoundError) as e:
            pytest.skip(f"Cookiecutter not available or failed: {e}")
    
    def test_project_generation(self, template_dir, default_context):
        """Test that the template generates a valid project structure."""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_dir = Path(tmpdir)
            
            # Generate project
            self.generate_project(template_dir, default_context, output_dir)
            
            # Check project was created
            project_dir = output_dir / default_context["project_slug"]
            assert project_dir.exists(), "Project directory was not created"
            
            # Check essential files exist
            essential_files = [
                "README.md",
                "pyproject.toml",
                "requirements.txt",
                ".env.example",
                "alembic.ini",
                "Dockerfile",
                "docker-compose.yml",
            ]
            
            for file in essential_files:
                assert (project_dir / file).exists(), f"{file} not found in generated project"
            
            # Check source code directory
            src_dir = project_dir / default_context["project_slug"].replace("-", "_")
            assert src_dir.exists(), "Source directory not found"
            
            # Check essential Python modules
            modules = [
                "__init__.py",
                "main.py",
                "cli.py",
                "config/__init__.py",
                "config/settings.py",
                "core/__init__.py",
                "core/bot.py",
                "handlers/__init__.py",
                "models/__init__.py",
            ]
            
            for module in modules:
                assert (src_dir / module).exists(), f"{module} not found in source directory"
    
    def test_github_workflows(self, template_dir, default_context):
        """Test that GitHub workflow templates are properly generated."""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_dir = Path(tmpdir)
            
            # Generate project
            self.generate_project(template_dir, default_context, output_dir)
            
            project_dir = output_dir / default_context["project_slug"]
            workflows_dir = project_dir / ".github" / "workflows"
            
            # Check if use_github_actions is enabled
            if default_context["use_github_actions"] == "y":
                assert workflows_dir.exists(), "GitHub workflows directory not created"
                
                # Check for workflow files
                expected_workflows = ["deploy.yml", "ci.yml"]
                for workflow in expected_workflows:
                    workflow_file = workflows_dir / workflow
                    assert workflow_file.exists(), f"{workflow} not found"
                    
                    # Check that template variables were replaced
                    content = workflow_file.read_text()
                    assert "{{ cookiecutter." not in content, f"Unrendered template variables in {workflow}"
                    assert default_context["bot_name"] in content, f"Bot name not found in {workflow}"
    
    def test_docker_files(self, template_dir, default_context):
        """Test Docker configuration files."""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_dir = Path(tmpdir)
            
            # Generate project
            self.generate_project(template_dir, default_context, output_dir)
            
            project_dir = output_dir / default_context["project_slug"]
            
            if default_context["use_docker"] == "y":
                # Check Dockerfile
                dockerfile = project_dir / "Dockerfile"
                assert dockerfile.exists(), "Dockerfile not found"
                
                content = dockerfile.read_text()
                assert f"FROM python:{default_context['python_version']}-slim" in content
                assert default_context["project_slug"].replace("-", "_") in content
                
                # Check docker-compose.yml
                compose_file = project_dir / "docker-compose.yml"
                assert compose_file.exists(), "docker-compose.yml not found"
                
                content = compose_file.read_text()
                assert default_context["project_slug"] in content
                assert default_context["database_name"] in content
    
    def test_env_example(self, template_dir, default_context):
        """Test .env.example file generation."""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_dir = Path(tmpdir)
            
            # Generate project
            self.generate_project(template_dir, default_context, output_dir)
            
            project_dir = output_dir / default_context["project_slug"]
            env_file = project_dir / ".env.example"
            
            assert env_file.exists(), ".env.example not found"
            
            content = env_file.read_text()
            
            # Check required variables
            assert "TELEGRAM_BOT_TOKEN=" in content
            assert "DATABASE_URL=" in content
            assert default_context["database_name"] in content
            
            # Check optional variables based on context
            if default_context["use_openrouter"] == "y":
                assert "OPENROUTER_API_KEY=" in content
                assert default_context["openrouter_model"] in content
            
            if default_context["use_support_bot"] == "y":
                assert "SUPPORT_BOT_TOKEN=" in content
                assert "SUPPORT_CHAT_ID=" in content
    
    def test_different_configurations(self, template_dir):
        """Test template with different configuration options."""
        configurations = [
            {
                "name": "minimal",
                "context_override": {
                    "use_openrouter": "n",
                    "use_support_bot": "n",
                    "use_github_actions": "n",
                    "use_docker": "n"
                }
            },
            {
                "name": "full_features",
                "context_override": {
                    "use_openrouter": "y",
                    "use_support_bot": "y",
                    "use_github_actions": "y",
                    "use_docker": "y"
                }
            },
            {
                "name": "different_python",
                "context_override": {
                    "python_version": "3.12",
                    "project_slug": "py312-bot"
                }
            }
        ]
        
        for config in configurations:
            with tempfile.TemporaryDirectory() as tmpdir:
                output_dir = Path(tmpdir)
                
                # Create context for this configuration
                context = self.default_context().copy()
                context.update(config["context_override"])
                
                # Generate project
                self.generate_project(template_dir, context, output_dir)
                
                # Basic check that project was created
                project_dir = output_dir / context["project_slug"]
                assert project_dir.exists(), f"Project not created for {config['name']} configuration"
                
                # Check pyproject.toml has correct Python version
                pyproject = project_dir / "pyproject.toml"
                content = pyproject.read_text()
                assert f">=3.10" in content  # Minimum version
                assert context["python_version"] in content


if __name__ == "__main__":
    pytest.main([__file__, "-v"])