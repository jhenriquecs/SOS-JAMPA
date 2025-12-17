/**
 * Gerencia a troca de abas no painel administrativo.
 * Oculta todo o conteúdo das abas e exibe apenas o conteúdo da aba selecionada.
 * @param {Event} evt - O evento de clique.
 * @param {string} tabName - O ID do elemento de conteúdo da aba a ser exibida.
 */
function openTab(evt, tabName) {
  var i, tabcontent, tablinks;

  // Oculta todo o conteúdo das abas
  tabcontent = document.getElementsByClassName("tab-content");
  for (i = 0; i < tabcontent.length; i++) {
    tabcontent[i].style.display = "none";
    tabcontent[i].classList.remove("active");
  }

  // Remove a classe 'active' de todos os botões de aba
  tablinks = document.getElementsByClassName("tab-btn");
  for (i = 0; i < tablinks.length; i++) {
    tablinks[i].className = tablinks[i].className.replace(" active", "");
  }

  // Exibe a aba atual e adiciona a classe 'active' ao botão clicado
  document.getElementById(tabName).style.display = "block";
  document.getElementById(tabName).classList.add("active");
  evt.currentTarget.className += " active";
}

/**
 * Exibe o modal de banimento de usuário.
 * Preenche o campo oculto de email com o email do usuário selecionado.
 * @param {string} email - O email do usuário a ser banido.
 */
function showBanModal(email) {
  document.getElementById("banEmail").value = email;
  document.getElementById("banModal").style.display = "flex";
}

/**
 * Fecha o modal de banimento de usuário.
 */
function closeBanModal() {
  document.getElementById("banModal").style.display = "none";
}
