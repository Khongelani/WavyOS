import { Component, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';

@Component({
  selector: 'app-founder-commitment',
  standalone: true,
  imports: [CommonModule],
  template: `
    @if (visible) {
      <div class="commitment-banner">
        <span class="commitment-text">
          This week WavyOS exists for one reason: pipeline.
        </span>
        <div class="commitment-actions">
          <button class="commit-btn" (click)="dismiss()">I will send before I refine</button>
          <button class="dismiss-link" (click)="dismiss()">Dismiss</button>
        </div>
      </div>
    }
  `,
  styleUrl: './founder-commitment.component.scss',
})
export class FounderCommitmentComponent implements OnInit {
  visible = false;

  private weekKey(): string {
    const today = new Date();
    const monday = new Date(today);
    monday.setDate(today.getDate() - today.getDay() + 1);
    return monday.toISOString().slice(0, 10);
  }

  ngOnInit(): void {
    const today = new Date();
    const isMonday = today.getDay() === 1;
    const key = `wavyos_committed_${this.weekKey()}`;
    const alreadyDone = localStorage.getItem(key);

    // Show on Monday if not yet dismissed this week
    if (isMonday && !alreadyDone) {
      this.visible = true;
    }
  }

  dismiss(): void {
    localStorage.setItem(`wavyos_committed_${this.weekKey()}`, '1');
    this.visible = false;
  }
}
