import { Component } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormBuilder, FormGroup, Validators, ReactiveFormsModule } from '@angular/forms';
import { Router } from '@angular/router';
import { AuthService } from '../../core/services/auth.service';

@Component({
  selector: 'app-login',
  standalone: true,
  imports: [CommonModule, ReactiveFormsModule],
  template: `
    <div class="login-shell">
      <div class="login-card">
        <div class="login-brand">
          <div class="brand-mark">W</div>
          <h1>WavyOS</h1>
          <p>Founder Operating System</p>
        </div>

        <form [formGroup]="form" (ngSubmit)="submit()" class="login-form">
          @if (error) {
            <div class="error-banner">{{ error }}</div>
          }

          <div class="field">
            <label>Email</label>
            <input type="email" formControlName="email" placeholder="your@email.com" autocomplete="email">
          </div>

          <div class="field">
            <label>Password</label>
            <input type="password" formControlName="password" placeholder="••••••••" autocomplete="current-password">
          </div>

          <button type="submit" class="btn-primary" [disabled]="loading || form.invalid">
            @if (loading) { <span>Signing in...</span> }
            @else { <span>Sign In</span> }
          </button>
        </form>
      </div>
    </div>
  `,
  styleUrl: './login.component.scss',
})
export class LoginComponent {
  form: FormGroup;
  loading = false;
  error = '';

  constructor(private fb: FormBuilder, private auth: AuthService, private router: Router) {
    this.form = this.fb.group({
      email: ['', [Validators.required, Validators.email]],
      password: ['', Validators.required],
    });
    if (this.auth.isLoggedIn()) {
      this.router.navigate(['/']);
    }
  }

  submit(): void {
    if (this.form.invalid) return;
    this.loading = true;
    this.error = '';
    const { email, password } = this.form.value;
    this.auth.login(email, password).subscribe({
      next: () => this.router.navigate(['/']),
      error: (err) => {
        this.error = err.error?.detail || 'Invalid credentials';
        this.loading = false;
      },
    });
  }
}
