// document.addEventListener('DOMContentLoaded', function () {
//   const pwd = document.getElementById('password');
//   const cpwd = document.getElementById('confirm_password');
//   const submitBtn = document.querySelector('button[type="submit"]');
//   // Create feedback elements if not present
//   let feedback = document.getElementById('pw-feedback');
//   if (!feedback) {
//     feedback = document.createElement('div');
//     feedback.id = 'pw-feedback';
//     feedback.className = 'mt-2';
//     // place feedback after confirm_password field
//     const cpwdDiv = cpwd.closest('.col-md-6') || cpwd.parentElement;
//     cpwdDiv.appendChild(feedback);
//   }

//   let strengthBar = document.getElementById('pw-strength');
//   if (!strengthBar) {
//     strengthBar = document.createElement('div');
//     strengthBar.id = 'pw-strength';
//     strengthBar.className = 'mt-2';
//     // place strength bar after password field
//     const pwdDiv = pwd.closest('.col-md-6') || pwd.parentElement;
//     pwdDiv.appendChild(strengthBar);
//   }

//   // Password strength helper (returns score 0..4 and label)
//   function passwordStrength(p) {
//     let score = 0;
//     if (!p) return {score: 0, label: 'Empty'};
//     if (p.length >= 8) score++;
//     if (/[A-Z]/.test(p) && /[a-z]/.test(p)) score++;
//     if (/\d/.test(p)) score++;
//     if (/[^A-Za-z0-9]/.test(p)) score++;
//     const labels = ['Very weak','Weak','Okay','Strong','Very strong'];
//     return {score, label: labels[score]};
//   }

//   function renderStrength(p) {
//     const {score, label} = passwordStrength(p);
//     // simple colored bar using bootstrap classes
//     const width = (score / 4) * 100;
//     const colorClass = score < 2 ? 'bg-danger' : (score === 2 ? 'bg-warning' : 'bg-success');
//     strengthBar.innerHTML = `
//       <div class="progress" style="height:6px;">
//         <div class="progress-bar ${colorClass}" role="progressbar" style="width:${width}%"></div>
//       </div>
//       <small class="text-muted">${label}</small>
//     `;
//   }

//   function renderMatch(p, cp) {
//     if (!p && !cp) {
//       feedback.innerHTML = '';
//       pwd.classList.remove('is-invalid','is-valid');
//       cpwd.classList.remove('is-invalid','is-valid');
//       return;
//     }
//     if (p === cp) {
//       feedback.innerHTML = '<div class="text-success small">Passwords match ✅</div>';
//       pwd.classList.add('is-valid'); pwd.classList.remove('is-invalid');
//       cpwd.classList.add('is-valid'); cpwd.classList.remove('is-invalid');
//     } else {
//       feedback.innerHTML = '<div class="text-danger small">Passwords do not match ❌</div>';
//       pwd.classList.add('is-invalid'); pwd.classList.remove('is-valid');
//       cpwd.classList.add('is-invalid'); cpwd.classList.remove('is-valid');
//     }
//   }

//   // enable/disable submit: require non-empty, match, and decent strength
//   function updateSubmitState() {
//     const p = pwd.value;
//     const cp = cpwd.value;
//     const {score} = passwordStrength(p);
//     const canSubmit = p && cp && (p === cp) && score >= 2; // adjust score threshold if you want
//     submitBtn.disabled = !canSubmit;
//   }

//   // initial state
//   renderStrength(pwd.value);
//   renderMatch(pwd.value, cpwd.value);
//   updateSubmitState();

//   // Listen to typing (input event)
//   [pwd, cpwd].forEach(input => {
//     input.addEventListener('input', function () {
//       renderStrength(pwd.value);
//       renderMatch(pwd.value, cpwd.value);
//       updateSubmitState();
//     });
//   });

//   // Optional: prevent form submit if JS missed something
//   const form = document.querySelector('form');
//   form.addEventListener('submit', function(e) {
//     const p = pwd.value, cp = cpwd.value;
//     const {score} = passwordStrength(p);
//     if (!p || p !== cp || score < 2) {
//       e.preventDefault();
//       // show a visible alert if needed
//       const area = document.getElementById('client-alert-area') || document.body;
//       const el = document.createElement('div');
//       el.className = 'alert alert-danger alert-dismissible fade show mt-2';
//       el.innerHTML = 'Fix password: make sure passwords match and are strong enough.<button type="button" class="btn-close" data-bs-dismiss="alert"></button>';
//       area.prepend(el);
//     }
//   });
// });
    const form = document.querySelector("form");
    const password = document.getElementById("password");
    const confirm_password = document.getElementById("confirm_password");

    form.addEventListener("submit", function(event) {
        if (password.value !== confirm_password.value) {
            event.preventDefault(); // form submit rokega
            alert("Passwords do not match!");
        }
    });

window.addEventListener('DOMContentLoaded', (event) => {
    setTimeout(() => {
        let alerts = document.querySelectorAll('.alert');
            alerts.forEach(alert => {
                alert.style.display = 'none';
            });
        }, 3000); 
    });