
function openSignup() {
    document.getElementById('email').focus();
    window.scrollTo({ top: 0, behavior: 'smooth' });
}
function signup() {
    const email = document.getElementById('email').value.trim();
    if (!email || !email.includes('@')) {
        alert('Please enter a valid email to join TaskHero.');
        return;
    }
    // placeholder action — replace with API call
    alert('Thanks! ' + email + ' — we\'ll email you a magic link soon.');
}


// keyboard shortcut: 'n' to focus quick add
window.addEventListener('keydown', (e) => {
    if (e.key === 'n' && document.activeElement.tagName !== 'INPUT') {
        e.preventDefault();
        document.getElementById('email').focus();
    }
});
