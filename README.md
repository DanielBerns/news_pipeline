# **Content Analysis and NLP platform: a web pipeline**.

Write

## Github tips

### Is there a simple way to delete all tracking branches whose remote equivalent no longer exists?

https://stackoverflow.com/questions/7726949/remove-tracking-branches-no-longer-on-remote

git remote prune origin prunes tracking branches not on the remote.

git branch --merged lists branches that have been merged into the current branch.

xargs git branch -d deletes branches listed on standard input.

Be careful deleting branches listed by git branch --merged. The list could include master or other branches you'd prefer not to delete.

To give yourself the opportunity to edit the list before deleting branches, you could do the following in one line:

git branch --merged >/tmp/merged-branches && \
  vi /tmp/merged-branches && xargs git branch -d </tmp/merged-branches



