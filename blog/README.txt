VALCREST AUTOMATED BLOG

This package leaves the main website untouched.

The automation creates and updates files only inside /blog.
The only file outside /blog is .github/workflows/publish-blog.yml, which GitHub requires in that exact location to run scheduled automation.

After uploading:
1. Add repository secret OPENAI_API_KEY.
2. In Settings > Actions > General, set Workflow permissions to Read and write permissions.
3. Open Actions > Publish weekly CRE insight > Run workflow to test it.

The scheduled workflow runs every Monday and commits only changes under /blog.
