document.addEventListener('DOMContentLoaded', function() {
  const mobileMenuButton = document.getElementById('mobile-menu-button');
  const mobileMenu = document.getElementById('mobile-menu');

  if (mobileMenuButton && mobileMenu) {
    mobileMenuButton.addEventListener('click', function() {
      mobileMenu.classList.toggle('hidden');
    });
  }

  // Smooth scrolling for anchor links
  document.querySelectorAll('a[href^="#"]').forEach(anchor => {
    anchor.addEventListener('click', function (e) {
      e.preventDefault();

      document.querySelector(this.getAttribute('href')).scrollIntoView({
        behavior: 'smooth'
      });
    });
  });
});

// Password Toggle Functionality for Login
const passwordToggle = document.getElementById('passwordToggle');
const passwordInput = document.getElementById('passwordInput');

if (passwordToggle && passwordInput) {
  passwordToggle.addEventListener('click', function() {
    const type = passwordInput.getAttribute('type') === 'password' ? 'text' : 'password';
    passwordInput.setAttribute('type', type);
    // Toggle icon (you might want to change the SVG path or class here)
    this.querySelector('svg').innerHTML = type === 'password'
      ? '<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 12a3 3 0 11-6 0 3 3 0 016 0z"></path><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M2.458 12C3.732 7.943 7.523 5 12 5c4.478 0 8.268 2.943 9.542 7-1.274 4.057-5.064 7-9.542 7-4.477 0-8.268-2.943-9.542-7z"></path>'
      : '<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13.875 18.825A10.05 10.05 0 0112 19c-4.478 0-8.268-2.943-9.542-7 1.274-4.057 5.064-7 9.542-7 1.549 0 3.008.388 4.336 1.125m0 1.5V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2v-1.5M4 6h16M4 12h16M4 18h16"></path>'; // Example for an "eye-slash" icon
  });
}

// Client-side Form Validation for Login
const loginForm = document.getElementById('loginForm');
const usernameInput = document.getElementById('username');
const passwordInputLogin = document.getElementById('passwordInput'); // Renamed to avoid conflict
const usernameFeedback = document.getElementById('username-feedback');
const passwordFeedback = document.getElementById('password-feedback');

if (loginForm && usernameInput && passwordInputLogin) {
  const validateField = (input, feedbackElement, errorMessage) => {
    if (input.value.trim() === '') {
      input.classList.add('is-invalid');
      feedbackElement.textContent = errorMessage;
      return false;
    } else {
      input.classList.remove('is-invalid');
      feedbackElement.textContent = '';
      return true;
    }
  };

  usernameInput.addEventListener('input', () => {
    validateField(usernameInput, usernameFeedback, 'Le nom d\'utilisateur est requis.');
  });

  passwordInputLogin.addEventListener('input', () => {
    validateField(passwordInputLogin, passwordFeedback, 'Le mot de passe est requis.');
  });

  loginForm.addEventListener('submit', function(event) {
    const isUsernameValid = validateField(usernameInput, usernameFeedback, 'Le nom d\'utilisateur est requis.');
    const isPasswordValid = validateField(passwordInputLogin, passwordFeedback, 'Le mot de passe est requis.');

    if (!isUsernameValid || !isPasswordValid) {
      event.preventDefault(); // Prevent form submission if validation fails
    }
  });
}

// Password Toggle Functionality for Signup
const signupPasswordToggle = document.getElementById('signupPasswordToggle');
const signupPasswordInput = document.getElementById('signupPassword');
const signupConfirmPasswordToggle = document.getElementById('signupConfirmPasswordToggle');
const signupConfirmPasswordInput = document.getElementById('signupConfirmPassword');

function setupPasswordToggle(toggleButton, passwordInput) {
  if (toggleButton && passwordInput) {
    toggleButton.addEventListener('click', function() {
      const type = passwordInput.getAttribute('type') === 'password' ? 'text' : 'password';
      passwordInput.setAttribute('type', type);
      // Toggle icon (you might want to change the SVG path or class here)
      this.querySelector('svg').innerHTML = type === 'password'
        ? '<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 12a3 3 0 11-6 0 3 3 0 016 0z"></path><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M2.458 12C3.732 7.943 7.523 5 12 5c4.478 0 8.268 2.943 9.542 7-1.274 4.057-5.064 7-9.542 7-4.477 0-8.268-2.943-9.542-7z"></path>'
        : '<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13.875 18.825A10.05 10.05 0 0112 19c-4.478 0-8.268-2.943-9.542-7 1.274-4.057 5.064-7 9.542-7 1.549 0 3.008.388 4.336 1.125m0 1.5V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2v-1.5M4 6h16M4 12h16M4 18h16"></path>';
    });
  }
}

setupPasswordToggle(signupPasswordToggle, signupPasswordInput);
setupPasswordToggle(signupConfirmPasswordToggle, signupConfirmPasswordInput);


// Client-side Form Validation for Signup
const signupForm = document.getElementById('signupForm');
const signupUsernameInput = document.getElementById('signupUsername');
const signupPasswordInput = document.getElementById('signupPassword');
const signupConfirmPasswordInput = document.getElementById('signupConfirmPassword');
const signupRoleSelect = document.getElementById('signupRole');

const signupUsernameFeedback = document.getElementById('signupUsername-feedback');
const signupPasswordFeedback = document.getElementById('signupPassword-feedback');
const signupConfirmPasswordFeedback = document.getElementById('signupConfirmPassword-feedback');
const signupRoleFeedback = document.getElementById('signupRole-feedback');

if (signupForm && signupUsernameInput && signupPasswordInput && signupConfirmPasswordInput && signupRoleSelect) {

  const validateSignupField = (input, feedbackElement, errorMessage) => {
    if (input.value.trim() === '') {
      input.classList.add('is-invalid');
      feedbackElement.textContent = errorMessage;
      return false;
    } else {
      input.classList.remove('is-invalid');
      feedbackElement.textContent = '';
      return true;
    }
  };

  const validatePasswordComplexity = (password, feedbackElement) => {
    const minLength = 8;
    const hasUpperCase = /[A-Z]/.test(password);
    const hasLowerCase = /[a-z]/.test(password);
    const hasNumber = /[0-9]/.test(password);
    const hasSpecialChar = /[!@#$%^&*(),.?":{}|<>]/.test(password);

    let isValid = true;
    let messages = [];

    if (password.length < minLength) {
      messages.push(`Doit contenir au moins ${minLength} caractères.`);
      isValid = false;
    }
    if (!hasUpperCase) {
      messages.push('Doit contenir au moins une majuscule.');
      isValid = false;
    }
    if (!hasLowerCase) {
      messages.push('Doit contenir au moins une minuscule.');
      isValid = false;
    }
    if (!hasNumber) {
      messages.push('Doit contenir au moins un chiffre.');
      isValid = false;
    }
    if (!hasSpecialChar) {
      messages.push('Doit contenir au moins un caractère spécial.');
      isValid = false;
    }

    if (!isValid) {
      signupPasswordInput.classList.add('is-invalid');
      feedbackElement.innerHTML = messages.map(msg => `<li>${msg}</li>`).join('');
    } else {
      signupPasswordInput.classList.remove('is-invalid');
      feedbackElement.textContent = '';
    }
    return isValid;
  };

  const validateConfirmPassword = () => {
    if (signupPasswordInput.value !== signupConfirmPasswordInput.value) {
      signupConfirmPasswordInput.classList.add('is-invalid');
      signupConfirmPasswordFeedback.textContent = 'Les mots de passe ne correspondent pas.';
      return false;
    } else {
      signupConfirmPasswordInput.classList.remove('is-invalid');
      signupConfirmPasswordFeedback.textContent = '';
      return true;
    }
  };

  const validateRole = () => {
    if (signupRoleSelect.value === '' || signupRoleSelect.value === 'default') { // Assuming 'default' is an invalid option
      signupRoleSelect.classList.add('is-invalid');
      signupRoleFeedback.textContent = 'Veuillez sélectionner un rôle.';
      return false;
    } else {
      signupRoleSelect.classList.remove('is-invalid');
      signupRoleFeedback.textContent = '';
      return true;
    }
  };

  signupUsernameInput.addEventListener('input', () => {
    validateSignupField(signupUsernameInput, signupUsernameFeedback, 'Le nom d\'utilisateur est requis.');
  });

  signupPasswordInput.addEventListener('input', () => {
    validateSignupField(signupPasswordInput, signupPasswordFeedback, 'Le mot de passe est requis.');
    validatePasswordComplexity(signupPasswordInput.value, signupPasswordFeedback);
    validateConfirmPassword(); // Re-validate confirm password when password changes
  });

  signupConfirmPasswordInput.addEventListener('input', validateConfirmPassword);

  signupRoleSelect.addEventListener('change', validateRole);

  signupForm.addEventListener('submit', function(event) {
    const isUsernameValid = validateSignupField(signupUsernameInput, signupUsernameFeedback, 'Le nom d\'utilisateur est requis.');
    const isPasswordValid = validateSignupField(signupPasswordInput, signupPasswordFeedback, 'Le mot de passe est requis.');
    const isPasswordComplex = validatePasswordComplexity(signupPasswordInput.value, signupPasswordFeedback);
    const isConfirmPasswordValid = validateConfirmPassword();
    const isRoleValid = validateRole();

    if (!isUsernameValid || !isPasswordValid || !isPasswordComplex || !isConfirmPasswordValid || !isRoleValid) {
      event.preventDefault(); // Prevent form submission if validation fails
    }
  });
}