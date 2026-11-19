use std::process::{Command, Output};

fn run(args: &[&str]) -> Output {
    Command::new(env!("CARGO_BIN_EXE_earshot-daemon")).args(args).output().unwrap()
}

fn stdout(out: &Output) -> String {
    String::from_utf8(out.stdout.clone()).unwrap()
}

fn stderr(out: &Output) -> String {
    String::from_utf8(out.stderr.clone()).unwrap()
}

fn expected_version() -> String {
    format!("earshot-daemon {}\n", env!("CARGO_PKG_VERSION"))
}

#[test]
fn version_long_flag() {
    let out = run(&["--version"]);
    assert_eq!(out.status.code(), Some(0));
    assert_eq!(stdout(&out), expected_version());
    assert_eq!(stderr(&out), "");
}

#[test]
fn version_short_flag() {
    let out = run(&["-V"]);
    assert_eq!(out.status.code(), Some(0));
    assert_eq!(stdout(&out), expected_version());
    assert_eq!(stderr(&out), "");
}

#[test]
fn help_long_flag() {
    let out = run(&["--help"]);
    let text = stdout(&out);
    assert_eq!(out.status.code(), Some(0));
    assert!(text.starts_with("Usage: earshot-daemon"), "{text}");
    assert!(text.contains("--version"), "{text}");
    assert!(text.contains("--help"), "{text}");
    assert_eq!(stderr(&out), "");
}

#[test]
fn help_short_flag() {
    let out = run(&["-h"]);
    let text = stdout(&out);
    assert_eq!(out.status.code(), Some(0));
    assert!(text.starts_with("Usage: earshot-daemon"), "{text}");
    assert_eq!(stderr(&out), "");
}

#[test]
fn no_args_prints_usage_to_stderr() {
    let out = run(&[]);
    assert_eq!(out.status.code(), Some(2));
    assert!(stderr(&out).starts_with("Usage: earshot-daemon"), "{}", stderr(&out));
    assert_eq!(stdout(&out), "");
}

#[test]
fn unknown_flag_is_rejected() {
    let out = run(&["--bogus"]);
    assert_eq!(out.status.code(), Some(2));
    assert!(stderr(&out).starts_with("Usage: earshot-daemon"), "{}", stderr(&out));
    assert_eq!(stdout(&out), "");
}

#[test]
fn extra_argument_after_version_is_rejected() {
    let out = run(&["--version", "extra"]);
    assert_eq!(out.status.code(), Some(2));
    assert!(stderr(&out).starts_with("Usage: earshot-daemon"), "{}", stderr(&out));
    assert_eq!(stdout(&out), "");
}

#[test]
fn extra_argument_after_help_is_rejected() {
    let out = run(&["--help", "extra"]);
    assert_eq!(out.status.code(), Some(2));
    assert_eq!(stdout(&out), "");
}
