source "https://rubygems.org"

# A FLOOR, DELIBERATELY NOT A PIN. `.ruby-version` is the pin and the only one.
#
# This exists because `.ruby-version` is not read by every tool that might be in
# front of you. asdf reads it only when `legacy_version_file = yes` is set in
# `~/.asdfrc`, which is per-user and off by default — so without this line, a
# contributor whose shell hands them the Ruby macOS ships (2.6) gets a confusing
# Jekyll error instead of a clear one. Bundler refuses first, and names the
# version it wanted.
#
# `>=` rather than `= 3.2.2` so that bumping `.ruby-version` stays a one-file
# change. Two files asserting one exact version is what this repository just
# stopped doing.
ruby ">= 3.2"

# Jekyll and nothing else. No theme gem, no plugins.
#
# If you find yourself adding a plugin, check first whether a _data file and a
# ten-line Liquid loop would do the same job. On this site it usually will.

gem "jekyll", "~> 4.3"

# Ruby 3.0+ dropped these from the standard library; Jekyll's local server
# needs them.
gem "webrick", "~> 1.8"
gem "csv"
gem "base64"
gem "bigdecimal"
