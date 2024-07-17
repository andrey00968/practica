document.addEventListener("DOMContentLoaded", function() {
    const formTitle = document.getElementById('form-title');
    const toggleAccountBtn = document.getElementById('toggle-account');
    const submitBtn = document.getElementById('submit-btn');

    toggleAccountBtn.addEventListener('click', function() {
        if (formTitle.textContent === "Регистрация") {
            formTitle.textContent = "Вход";
            toggleAccountBtn.textContent = "У меня нет аккаунта";
            submitBtn.textContent = "Войти";
            submitBtn.classList.remove('register-btn');
            submitBtn.classList.add('login-btn');
            toggleAccountBtn.classList.remove('toggle-btn');
            toggleAccountBtn.classList.add('no-account-btn');
        } else {
            formTitle.textContent = "Регистрация";
            toggleAccountBtn.textContent = "У меня уже есть аккаунт";
            submitBtn.textContent = "Регистрация";
            submitBtn.classList.remove('login-btn');
            submitBtn.classList.add('register-btn');
            toggleAccountBtn.classList.remove('no-account-btn');
            toggleAccountBtn.classList.add('toggle-btn');
        }
    });
});
