$(document).ready(function(){
  editor = new SimpleMDE({ 
    element: document.getElementById("editor"),
    promptURLs: true,
    spellChecker: false,
    showIcons: ["code", "table"],
    renderingConfig: {
      singleLineBreaks: false,
      codeSyntaxHighlighting: true,
    },
  });

  //样式调整，使得预览更加便利
  $(".fa-columns").click(function(){

  });
});

function getContent(){
  return editor.value();
}