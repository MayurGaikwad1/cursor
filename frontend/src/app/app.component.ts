import { Component, OnInit, OnDestroy } from '@angular/core';
import { Router, NavigationEnd } from '@angular/router';
import { Subject } from 'rxjs';
import { takeUntil, filter } from 'rxjs/operators';

import { AuthService } from './core/services/auth.service';
import { LoadingService } from './core/services/loading.service';
import { NotificationService } from './core/services/notification.service';
import { ThemeService } from './core/services/theme.service';

@Component({
  selector: 'app-root',
  templateUrl: './app.component.html',
  styleUrls: ['./app.component.scss']
})
export class AppComponent implements OnInit, OnDestroy {
  title = 'ELAMS - Enterprise Logical Access Management System';
  private destroy$ = new Subject<void>();
  
  isAuthenticated$ = this.authService.isAuthenticated$;
  currentUser$ = this.authService.currentUser$;
  isLoading$ = this.loadingService.isLoading$;
  
  sidenavOpened = true;
  
  navigationItems = [
    {
      label: 'Dashboard',
      icon: 'dashboard',
      route: '/dashboard',
      permission: 'dashboard:read'
    },
    {
      label: 'Users',
      icon: 'people',
      route: '/users',
      permission: 'user:read'
    },
    {
      label: 'Roles & Permissions',
      icon: 'admin_panel_settings',
      route: '/roles',
      permission: 'role:read'
    },
    {
      label: 'Organizations',
      icon: 'business',
      route: '/organizations',
      permission: 'organization:read'
    },
    {
      label: 'Sessions',
      icon: 'laptop',
      route: '/sessions',
      permission: 'session:read'
    },
    {
      label: 'Audit Logs',
      icon: 'history',
      route: '/audit',
      permission: 'audit:read'
    },
    {
      label: 'Policies',
      icon: 'policy',
      route: '/policies',
      permission: 'policy:read'
    },
    {
      label: 'Reports',
      icon: 'assessment',
      route: '/reports',
      permission: 'report:read'
    },
    {
      label: 'Settings',
      icon: 'settings',
      route: '/settings',
      permission: 'settings:read'
    }
  ];
  
  constructor(
    private router: Router,
    private authService: AuthService,
    private loadingService: LoadingService,
    private notificationService: NotificationService,
    private themeService: ThemeService
  ) {}
  
  ngOnInit(): void {
    this.initializeApp();
    this.setupRouterEvents();
    this.setupAuthEvents();
  }
  
  ngOnDestroy(): void {
    this.destroy$.next();
    this.destroy$.complete();
  }
  
  private initializeApp(): void {
    // Initialize theme
    this.themeService.initializeTheme();
    
    // Check authentication status on app start
    this.authService.checkAuthStatus();
    
    // Setup session timeout monitoring
    this.authService.startSessionMonitoring();
  }
  
  private setupRouterEvents(): void {
    this.router.events
      .pipe(
        filter(event => event instanceof NavigationEnd),
        takeUntil(this.destroy$)
      )
      .subscribe((event: NavigationEnd) => {
        // Handle route changes
        this.handleRouteChange(event.url);
      });
  }
  
  private setupAuthEvents(): void {
    // Listen for authentication events
    this.authService.authEvents$
      .pipe(takeUntil(this.destroy$))
      .subscribe(event => {
        switch (event.type) {
          case 'LOGIN_SUCCESS':
            this.notificationService.showSuccess('Welcome back!');
            break;
          case 'LOGOUT':
            this.notificationService.showInfo('You have been logged out');
            this.router.navigate(['/auth/login']);
            break;
          case 'SESSION_EXPIRED':
            this.notificationService.showWarning('Your session has expired. Please log in again.');
            this.router.navigate(['/auth/login']);
            break;
          case 'TOKEN_REFRESHED':
            // Silent refresh - no notification needed
            break;
        }
      });
  }
  
  private handleRouteChange(url: string): void {
    // Close sidenav on mobile after navigation
    if (window.innerWidth < 768) {
      this.sidenavOpened = false;
    }
    
    // Update page title based on route
    this.updatePageTitle(url);
  }
  
  private updatePageTitle(url: string): void {
    const routeItem = this.navigationItems.find(item => url.startsWith(item.route));
    if (routeItem) {
      document.title = `${routeItem.label} - ELAMS`;
    } else {
      document.title = 'ELAMS - Enterprise Access Management';
    }
  }
  
  toggleSidenav(): void {
    this.sidenavOpened = !this.sidenavOpened;
  }
  
  logout(): void {
    this.authService.logout();
  }
  
  navigateToProfile(): void {
    this.router.navigate(['/profile']);
  }
  
  navigateToSettings(): void {
    this.router.navigate(['/settings']);
  }
  
  hasPermission(permission: string): boolean {
    return this.authService.hasPermission(permission);
  }
}