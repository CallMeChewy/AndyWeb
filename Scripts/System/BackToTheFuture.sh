# 🧼 Single Command to Return to Present (and purge time machine debris)
git switch main && git fetch origin && git reset --hard origin/main && git branch | grep travel_ | xargs -n 1 git branch -D
