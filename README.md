This website is being generated using [Quarto](https://quarto.org/docs/websites).
As of now, the source is is simply the annotation-pilot wiki embedded as a submodule. This is why this repo needs to be cloned recursively: `git clone --recursive git@github.com:MusicalForm/guidelines.git`.

When you have [Quarto installed](https://quarto.org/docs/get-started/) you can render the homepage via `quarto render`. To preview, do `quarto preview`. The preview in your browser will update once you save changes to any of the source files.

**To modify**

* Make the changes in the wiki or directly in the submodule:
    * When you modify the wiki in the browser, you need then to update the submodule of this repo `git submodule update` so that it reflects these changes.
    * When you modify the wiki locally in the submodule, you need to commit and push the changes (for this you need to navigate into the submodule so that the git commands are executed there, not in the parent `guidelines`).
* Then `quarto render`:
    * Commit the changed homepage in the `docs` folder together with the updated submodule (which is now pointing to to the latest commit).
    * A few seconds after you push, the homepage will update.
