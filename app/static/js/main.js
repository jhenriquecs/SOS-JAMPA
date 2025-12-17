/**
 * Redireciona para login via POST sem expor mensagem na URL.
 */
function redirectToLogin(reasonText) {
  const loginUrl = (window.APP_ROUTES && window.APP_ROUTES.login) || "/auth/login";
  const form = document.createElement("form");
  form.method = "POST";
  form.action = loginUrl;

  const reason = document.createElement("input");
  reason.type = "hidden";
  reason.name = "reason";
  reason.value = reasonText || "";
  form.appendChild(reason);

  const reasonOnly = document.createElement("input");
  reasonOnly.type = "hidden";
  reasonOnly.name = "reason_only";
  reasonOnly.value = "1";
  form.appendChild(reasonOnly);

  document.body.appendChild(form);
  form.submit();
}

/**
 * Gerencia o clique no botão "expandir" dos cards de resíduos.
 * Alterna a visibilidade dos detalhes do card.
 */
document.addEventListener("click", (e) => {
  if (e.target.matches(".btn-expand")) {
    e.preventDefault();
    e.stopPropagation();

    const targetId = e.target.getAttribute("data-target");
    const details = document.getElementById(targetId);

    if (!details) return;

    details.classList.toggle("hidden");
    e.target.innerText = details.classList.contains("hidden")
      ? "Ver detalhes"
      : "Ocultar detalhes";
  }
});

/**
 * Função auxiliar para filtrar pontos de coleta
 */
function filterPoints(lat, lon) {
  const radiusInput = document.getElementById("radiusInput");
  const maxDist = parseFloat(radiusInput ? radiusInput.value : 50);

  document.querySelectorAll(".waste-card").forEach((card) => {
    const details = card.querySelector(".waste-details");
    const listItems = card.querySelectorAll(".locations li");
    const locs = [...listItems].map((li) => ({
      element: li,
      lat: parseFloat(li.dataset.lat),
      lon: parseFloat(li.dataset.lon),
      address: li.textContent.trim(),
    }));

    if (locs.length === 0) return;

    let countFound = 0;

    locs.forEach((loc) => {
      // Oculta inicialmente
      loc.element.style.display = "none";

      if (
        !isNaN(loc.lat) &&
        !isNaN(loc.lon) &&
        loc.lat !== 0 &&
        loc.lon !== 0
      ) {
        const d = distance(lat, lon, loc.lat, loc.lon);
        // Mostra se estiver dentro do raio
        if (d <= maxDist) {
          loc.element.style.display = "block";
          countFound++;
        }
      }
    });

    const infoDiv = details.querySelector(".nearest-info");

    if (countFound > 0) {
      if (infoDiv) {
        infoDiv.textContent = `${countFound} ponto(s) encontrado(s) no raio de ${maxDist} km.`;
        infoDiv.style.color = "var(--primary-color)";
      }

      // Open details
      details.classList.remove("hidden");
      card.querySelector(".btn-expand").innerText = "Ocultar detalhes";
    } else {
      if (infoDiv) {
        infoDiv.textContent = `Nenhum ponto encontrado no raio de ${maxDist} km.`;
        infoDiv.style.color = "#e74c3c";
      }
    }
  });
}

/**
 * Gerencia o clique no botão "Usar GPS".
 */
document.getElementById("useLocation")?.addEventListener("click", () => {
  if (!navigator.geolocation) {
    alert("Geolocalização não disponível");
    return;
  }

  navigator.geolocation.getCurrentPosition(
    (pos) => {
      filterPoints(pos.coords.latitude, pos.coords.longitude);
    },
    (err) => {
      console.warn("GPS falhou, tentando localização por IP...", err);

      // Tenta fallback via IP (útil para desktops sem GPS)
      fetch("https://ipapi.co/json/")
        .then((res) => res.json())
        .then((data) => {
          if (data.latitude && data.longitude) {
            // Sucesso no fallback
            alert(
              `GPS indisponível. Usando localização aproximada (IP): ${
                data.city || "Desconhecida"
              }`
            );
            filterPoints(data.latitude, data.longitude);
          } else {
            throw new Error("Dados de localização IP inválidos");
          }
        })
        .catch((ipErr) => {
          console.error("Fallback IP falhou:", ipErr);

          // Se falhar o fallback, mostra o erro original do GPS
          let msg = "Erro desconhecido.";
          switch (err.code) {
            case err.PERMISSION_DENIED:
              msg = "Permissão negada. Verifique se o navegador tem permissão.";
              break;
            case err.POSITION_UNAVAILABLE:
              msg =
                "Localização indisponível. Verifique se o GPS do Windows está ativado.";
              break;
            case err.TIMEOUT:
              msg = "Tempo limite esgotado.";
              break;
          }
          alert(
            "Não foi possível obter localização: " +
              msg +
              "\n\nPor favor, digite seu endereço manualmente no campo de busca."
          );
        });
    },
    {
      enableHighAccuracy: true,
      timeout: 10000,
      maximumAge: 0,
    }
  );
});

/**
 * Gerencia o clique no botão "Buscar" (por endereço).
 */
document
  .getElementById("searchLocation")
  ?.addEventListener("click", async () => {
    const addressInput = document.getElementById("addressInput");
    const address = addressInput.value.trim();

    if (!address) {
      alert("Por favor, digite um endereço.");
      return;
    }

    try {
      const response = await fetch("/geocode", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({ address: address }),
      });

      const data = await response.json();

      if (response.ok) {
        filterPoints(data.lat, data.lon);
      } else {
        alert(data.error || "Erro ao buscar endereço.");
      }
    } catch (error) {
      console.error("Erro na requisição:", error);
      alert("Erro ao conectar com o servidor.");
    }
  });

function distance(lat1, lon1, lat2, lon2) {
  const R = 6371; // Radius of the earth in km
  const dLat = deg2rad(lat2 - lat1);
  const dLon = deg2rad(lon2 - lon1);
  const a =
    Math.sin(dLat / 2) * Math.sin(dLat / 2) +
    Math.cos(deg2rad(lat1)) *
      Math.cos(deg2rad(lat2)) *
      Math.sin(dLon / 2) *
      Math.sin(dLon / 2);
  const c = 2 * Math.atan2(Math.sqrt(a), Math.sqrt(1 - a));
  return R * c; // Distance in km
}

function deg2rad(deg) {
  return deg * (Math.PI / 180);
}

// ===== Toggle de visibilidade de senha =====
const toggleSenha = document.getElementById("toggle-senha");
if (toggleSenha) {
  toggleSenha.addEventListener("click", function (e) {
    e.preventDefault();
    const senhaInput = document.getElementById("senha");
    const tipo = senhaInput.type === "password" ? "text" : "password";
    senhaInput.type = tipo;
    this.innerHTML =
      tipo === "password"
        ? '<i class="fas fa-eye"></i>'
        : '<i class="fas fa-eye-slash"></i>';
  });
}

const toggleConfirmar = document.getElementById("toggle-confirmar");
if (toggleConfirmar) {
  toggleConfirmar.addEventListener("click", function (e) {
    e.preventDefault();
    const confirmarInput = document.getElementById("confirmar_senha");
    const tipo = confirmarInput.type === "password" ? "text" : "password";
    confirmarInput.type = tipo;
    this.innerHTML =
      tipo === "password"
        ? '<i class="fas fa-eye"></i>'
        : '<i class="fas fa-eye-slash"></i>';
  });
}

// ===== Validação de requisitos de senha em tempo real =====
const senha = document.getElementById("senha");
if (senha) {
  senha.addEventListener("input", () => {
    const valor = senha.value;

    // Verifica cada requisito e atualiza a classe CSS
    const reqMin = document.getElementById("req-min");
    if (reqMin) reqMin.classList.toggle("ok", valor.length >= 8);

    const reqMai = document.getElementById("req-mai");
    if (reqMai) reqMai.classList.toggle("ok", /[A-Z]/.test(valor));

    const reqMinu = document.getElementById("req-minu");
    if (reqMinu) reqMinu.classList.toggle("ok", /[a-z]/.test(valor));

    const reqNum = document.getElementById("req-num");
    if (reqNum) reqNum.classList.toggle("ok", /\d/.test(valor));

    const reqEsp = document.getElementById("req-esp");
    if (reqEsp) reqEsp.classList.toggle("ok", /[@$!%*?&#]/.test(valor));
  });
}

/* ===== Lógica do Widget de Criar Post ===== */

/**
 * Alterna a visibilidade dos campos de input (endereço, tags) no widget.
 * @param {string} id - O ID do elemento a ser alternado.
 */
function toggleCpInput(id) {
  const el = document.getElementById(id);
  if (el.classList.contains("hidden-input")) {
    el.classList.remove("hidden-input");
    el.focus();
  } else {
    el.classList.add("hidden-input");
  }
}

/**
 * Inicializa o comportamento do widget de postagem.
 * Expande o widget quando o campo de descrição recebe foco.
 */
document.addEventListener("DOMContentLoaded", function () {
  const cpDesc = document.getElementById("cp-desc");
  const cpExtras = document.getElementById("cp-extras");
  const cpActions = document.getElementById("cp-actions");

  if (cpDesc) {
    cpDesc.addEventListener("focus", () => {
      cpExtras.classList.remove("hidden-initially");
      cpActions.classList.remove("hidden-initially");
    });
  }
});

/**
 * Envia uma requisição para curtir/descurtir um post.
 * Atualiza a interface com o novo número de curtidas e o estado do botão.
 * @param {string} postId - O ID do post.
 */
function toggleLike(postId) {
  fetch(`/posts/like/${postId}`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
  })
    .then((response) => {
      if (response.status === 401) {
        redirectToLogin("Você precisa estar logado para curtir posts.");
        return;
      }
      return response.json();
    })
    .then((data) => {
      if (data && data.error) {
        console.error(data.error);
        return;
      }

      if (data) {
        // Atualiza o contador (ID corrigido para bater com o HTML)
        const countSpan = document.getElementById(`likes-val-${postId}`);
        if (countSpan) {
          countSpan.textContent = data.likes_count;
        }

        // Atualiza o estilo do botão
        const btn = document.getElementById(`like-btn-${postId}`);
        if (btn) {
          if (data.liked) {
            btn.classList.add("liked");
            btn.style.color = "#1877f2"; // Azul do Facebook
          } else {
            btn.classList.remove("liked");
            btn.style.color = ""; // Remove cor inline para voltar ao CSS padrão
          }
        }
      }
    })
    .catch((err) => console.error("Erro ao curtir:", err));
}

/**
 * Compartilha o post usando a Web Share API ou copia o link.
 * @param {string} url - A URL do post para compartilhar.
 */
function sharePost(url) {
  // Garante URL absoluta
  const fullUrl = url.startsWith("http") ? url : window.location.origin + url;

  if (navigator.share) {
    navigator
      .share({
        title: "Confira este post no EcoPonto",
        url: fullUrl,
      })
      .catch(console.error);
  } else {
    // Fallback: Copiar para a área de transferência
    navigator.clipboard
      .writeText(fullUrl)
      .then(() => alert("Link copiado para a área de transferência!"))
      .catch((err) => console.error("Erro ao copiar:", err));
  }
}

/**
 * Alterna a visibilidade da seção de comentários e carrega os comentários se necessário.
 */
function toggleComments(postId) {
  const section = document.getElementById(`comments-section-${postId}`);
  if (!section) return;

  if (section.classList.contains("hidden")) {
    section.classList.remove("hidden");
    loadComments(postId);
    // Foca no input
    setTimeout(() => {
      const input = document.getElementById(`comment-input-${postId}`);
      if (input) input.focus();
    }, 100);
  } else {
    section.classList.add("hidden");
  }
}

/**
 * Carrega comentários via AJAX.
 */
function loadComments(postId) {
  const list = document.getElementById(`comments-list-${postId}`);
  if (!list) return;

  // Evita recarregar se já carregou (opcional)
  if (list.dataset.loaded === "true") return;

  list.innerHTML = '<div class="loading-comments">Carregando...</div>';

  fetch(`/posts/${postId}/comments`)
    .then((res) => res.json())
    .then((data) => {
      list.innerHTML = "";
      if (data.length === 0) {
        list.innerHTML =
          '<p class="no-comments">Seja o primeiro a comentar!</p>';
      } else {
        data.forEach((c) => {
          list.appendChild(createCommentElement(c));
        });
      }
      list.dataset.loaded = "true";
    })
    .catch((err) => {
      console.error(err);
      list.innerHTML = '<p class="error">Erro ao carregar comentários.</p>';
    });
}

/**
 * Cria o elemento HTML de um comentário.
 */
function createCommentElement(c) {
  const div = document.createElement("div");
  div.className = "comment-item";
  div.id = `comment-${c.id}`;
  // Ajuste do caminho da imagem
  const imgSrc = c.author_image
    ? "/static/" + c.author_image
    : `https://ui-avatars.com/api/?name=${encodeURIComponent(
        c.author_nick
      )}&background=random`;

  let deleteBtn = "";
  // c.can_delete vem do backend
  if (c.can_delete) {
    // Passamos postId também para atualizar contador
    // Como c.post_id pode não vir no objeto simplificado, vamos garantir que venha ou pegar do contexto
    // O backend get_comments não estava retornando post_id, vamos assumir que o chamador sabe ou adicionar no backend.
    // Vou adicionar post_id no backend response para garantir.
    deleteBtn = `<button class="delete-comment-btn" onclick="deleteComment('${
      c.id
    }', '${c.post_id || ""}')" title="Excluir">&times;</button>`;
  }

  div.innerHTML = `
        <img src="${imgSrc}" class="comment-avatar" alt="Avatar">
        <div class="comment-bubble-wrapper">
            <div class="comment-bubble">
                <div class="comment-author">${c.author_nick}</div>
                <div class="comment-text">${c.text}</div>
            </div>
            ${deleteBtn}
        </div>
    `;
  return div;
}

/**
 * Exclui um comentário.
 */
function deleteComment(commentId, postId) {
  if (!confirm("Excluir comentário?")) return;

  fetch(`/posts/comment/${commentId}/delete`, {
    method: "DELETE",
  })
    .then((res) => res.json())
    .then((data) => {
      if (data.success) {
        const el = document.getElementById(`comment-${commentId}`);
        if (el) el.remove();

        // Atualiza contador visualmente (decrementa)
        // Se postId não veio, tentamos achar pelo contexto do DOM se necessário, mas ideal é vir.
        if (postId) {
          const countSpan = document.getElementById(`comments-val-${postId}`);
          if (countSpan) {
            let current = parseInt(countSpan.textContent) || 0;
            countSpan.textContent = Math.max(0, current - 1);
          }
        }
      } else {
        alert(data.error || "Erro ao excluir");
      }
    })
    .catch((err) => console.error(err));
}

/**
 * Envia um novo comentário.
 */
function submitComment(postId) {
  const input = document.getElementById(`comment-input-${postId}`);
  const text = input.value.trim();
  if (!text) return;

  // Desabilita input enquanto envia
  input.disabled = true;

  fetch(`/posts/${postId}/comment`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ text: text }),
  })
    .then((res) => {
      if (res.status === 401) {
        redirectToLogin("Você precisa estar logado para comentar.");
        return;
      }
      return res.json();
    })
    .then((data) => {
      input.disabled = false;
      if (data.error) {
        alert(data.error);
        return;
      }

      const list = document.getElementById(`comments-list-${postId}`);
      const noComments = list.querySelector(".no-comments");
      if (noComments) noComments.remove();

      list.appendChild(createCommentElement(data));
      input.value = "";
      input.focus();

      // Atualiza contador
      const countSpan = document.getElementById(`comments-val-${postId}`);
      if (countSpan) countSpan.textContent = data.comments_count;
    })
    .catch((err) => {
      console.error(err);
      input.disabled = false;
      alert("Erro ao enviar comentário.");
    });
}

// Permite enviar com Enter
function checkEnter(event, postId) {
  if (event.key === "Enter") {
    submitComment(postId);
  }
}
