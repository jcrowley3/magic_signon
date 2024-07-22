#!/usr/bin/env bash
#
# These are all the "known good" Postman tests, run against a running Docker container:
#


# Knock yourself out:  https://patorjk.com/software/taag/#p=display&f=Doh&t=Test%20Failure
function show_error {
   cat <<'EOF'

   ______         __           ______      _ __                                                               
  / ____/___     / /_____     / ____/___ _(_) /                                                               
 / / __/ __ \   / __/ __ \   / /_  / __ `/ / /                                                                
/ /_/ / /_/ /  / /_/ /_/ /  / __/ / /_/ / / /                                                                 
\____/\____/   \__/\____/  /_/ __ \__,_/_/_/     ____          __     __  __________________ ___   ____  ____ 
   / __ \____     ____  ____  / /_   _________  / / /__  _____/ /_   / / / /_  __/_  __/ __ \__ \ / __ \/ __ \
  / / / / __ \   / __ \/ __ \/ __/  / ___/ __ \/ / / _ \/ ___/ __/  / /_/ / / /   / / / /_/ /_/ // / / / / / /
 / /_/ / /_/ /  / / / / /_/ / /_   / /__/ /_/ / / /  __/ /__/ /_   / __  / / /   / / / ____/ __// /_/ / /_/ / 
/_____/\____/  /_/ /_/\____/\__/   \___/\____/_/_/\___/\___/\__/  /_/ /_/ /_/   /_/ /_/   /____/\____/\____/  
                                                                                                              
EOF
   return
}

SOURCE_DIR=/app/tests/postman
tests=(
   "$SOURCE_DIR"/magic_signon_api.postman_collection.json
)

pass_count=0
fail_count=0

for test in "${tests[@]}"; do
   [ -f "$test" ] || break
   newman run $test
   status=$?
   if [ $status -ne 0 ]; then
      echo "There was a test failure in ${test}"
      failure_list+=(${test})
      fail_count=$((fail_count+1))
   else
      pass_count=$((pass_count+1))
   fi
done

if [ $fail_count -gt 0 ]; then
   echo
   echo "${fail_count} out of ${#tests[@]} collections failed."
   echo "There were test failures in the following collections:"
   for failure in "${failure_list[@]}"; do
      echo "${failure}"
   done
   show_error
   exit 1
else
   echo
   echo "All ${#tests[@]} collections passed."
fi
