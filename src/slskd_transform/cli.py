import click
from pathlib import Path

from slskd_transform.config import load_config
from slskd_transform.search import run_search
from slskd_transform.rename import run_rename


@click.group()
@click.option("--config", "-c", type=click.Path(exists=True), default=None, help="Path to config.yml")
@click.option("--host", type=str, default=None, help="slskd host URL")
@click.option("--api-key", type=str, default=None, help="slskd API key")
@click.option("--no-verify-ssl", is_flag=True, default=False, help="Disable SSL verification")
@click.option("--threads", "-t", type=int, default=None, help="Number of search threads")
@click.pass_context
def cli(ctx, config, host, api_key, no_verify_ssl, threads):
    """slskd-transform: Bulk-upgrade your music library from lossy to lossless."""
    ctx.ensure_object(dict)
    ctx.obj["config_path"] = Path(config) if config else None
    ctx.obj["cli_overrides"] = {}
    if host is not None:
        ctx.obj["cli_overrides"]["host"] = host
    if api_key is not None:
        ctx.obj["cli_overrides"]["api_key"] = api_key
    if no_verify_ssl:
        ctx.obj["cli_overrides"]["verify_ssl"] = False
    if threads is not None:
        ctx.obj["cli_overrides"]["num_threads"] = threads


@cli.command()
@click.option("--music-dir", "-m", type=click.Path(exists=True), default=None, help="Directory with lossy source files")
@click.option("--recursive", "-r", is_flag=True, default=None, help="Scan music directory recursively")
@click.option("--format", "-f", "fmt", type=str, default=None, help="Target format (default: flac)")
@click.option("--tolerance", type=int, default=None, help="Duration match tolerance in seconds")
@click.option("--timeout", type=int, default=None, help="Seconds to wait for search results")
@click.pass_context
def search(ctx, music_dir, recursive, fmt, tolerance, timeout):
    """Search Soulseek for lossless versions and enqueue downloads."""
    overrides = dict(ctx.obj["cli_overrides"])
    if music_dir is not None:
        overrides["music_dir"] = music_dir
    if recursive is not None:
        overrides["recursive"] = recursive
    if fmt is not None:
        overrides["format"] = fmt
    if tolerance is not None:
        overrides["duration_tolerance"] = tolerance
    if timeout is not None:
        overrides["search_timeout"] = timeout

    config = load_config(config_path=ctx.obj["config_path"], cli_overrides=overrides)

    if not config.api_key:
        raise click.ClickException(
            "No API key configured. Set SLSKD_API_KEY env var, add api_key to config.yml, or pass --api-key."
        )

    run_search(config)


@cli.command()
@click.option("--source-dir", "-s", type=click.Path(exists=True), default=None, help="Directory where slskd downloads land")
@click.option("--dest-dir", "-d", type=click.Path(), default=None, help="Destination for renamed files")
@click.pass_context
def rename(ctx, source_dir, dest_dir):
    """Rename downloaded FLACs to 'Artist - Title.flac' using metadata."""
    overrides = dict(ctx.obj["cli_overrides"])
    if source_dir is not None:
        overrides["source_dir"] = source_dir
    if dest_dir is not None:
        overrides["destination_dir"] = dest_dir

    config = load_config(config_path=ctx.obj["config_path"], cli_overrides=overrides)
    run_rename(config)
