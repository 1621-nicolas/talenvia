"use strict";
/* Mejoras progresivas: con JavaScript desactivado, los formularios siguen
 * funcionando y las validaciones del servidor siguen siendo obligatorias. */
document.addEventListener("DOMContentLoaded", () => {
  const registro = document.querySelector("[data-registro]");
  if (registro) {
    const rol = registro.querySelector('select[name="rol"]');
    const empresa = registro.querySelector("#datos-empresa");
    const aviso = registro.querySelector("#mensaje-rol");
    const alternar = () => {
      const empresarial = rol.value === "EMPRESA";
      empresa.hidden = !empresarial;
      empresa.querySelectorAll("input").forEach((campo) => {
        campo.required = empresarial;
        // Campos que el usuario no necesita para el rol seleccionado
        // quedan fuera del envío, sin depender de ello para seguridad.
        campo.disabled = !empresarial;
      });
      aviso.textContent = empresarial
        ? "Completa los datos empresariales. Tu empresa quedará pendiente de aprobación."
        : "Podrás completar tu perfil profesional y CV después del registro.";
    };
    rol.addEventListener("change", alternar);
    alternar();
  }

  // El control es accesible por teclado y anuncia su estado.
  document.querySelectorAll('input[type="password"]').forEach((campo) => {
    const envoltura = document.createElement("div");
    envoltura.className = "campo-contrasena";
    campo.parentNode.insertBefore(envoltura, campo);
    envoltura.appendChild(campo);
    const boton = document.createElement("button");
    boton.type = "button";
    boton.className = "mostrar-contrasena";
    boton.textContent = "Mostrar";
    boton.setAttribute("aria-label", "Mostrar contraseña");
    boton.setAttribute("aria-pressed", "false");
    if (campo.id) boton.setAttribute("aria-controls", campo.id);
    boton.addEventListener("click", () => {
      const visible = campo.type === "password";
      campo.type = visible ? "text" : "password";
      boton.textContent = visible ? "Ocultar" : "Mostrar";
      boton.setAttribute("aria-label", visible ? "Ocultar contraseña" : "Mostrar contraseña");
      boton.setAttribute("aria-pressed", visible ? "true" : "false");
    });
    envoltura.appendChild(boton);
  });
});
