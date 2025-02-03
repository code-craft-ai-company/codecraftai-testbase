/* =======================================================================
    Author: "Myron Walker"
    Copyright: "Copyright 2025, Automation Mojo LLC"
 =======================================================================*/


let globalSheets = null;


function getGlobalStyleSheets() {
    if (globalSheets === null) {
        globalSheets = Array.from(document.styleSheets)
          .map(x => {
            const sheet = new CSSStyleSheet();
            const css = Array.from(x.cssRules).map(rule => rule.cssText).join(' ');
            sheet.replaceSync(css);
            return sheet;
          });
      }
    
      return globalSheets;
}


function addGlobalStylesToShadowRoot(shadowRoot) {
    shadowRoot.adoptedStyleSheets.push(
        ...getGlobalStyleSheets()
    );
}
