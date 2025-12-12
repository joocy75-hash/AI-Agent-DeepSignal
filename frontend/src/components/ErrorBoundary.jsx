import { Component } from 'react';
import { Result, Button } from 'antd';

/**
 * Error Boundary Component
 * React 애플리케이션의 에러를 catch하고 fallback UI를 표시합니다.
 *
 * Features:
 * - 컴포넌트 트리의 에러 catch
 * - 에러 로깅
 * - 사용자 친화적인 에러 메시지
 * - 페이지 새로고침 옵션
 */
class ErrorBoundary extends Component {
  constructor(props) {
    super(props);
    this.state = {
      hasError: false,
      error: null,
      errorInfo: null,
    };
  }

  static getDerivedStateFromError(error) {
    // Update state so the next render will show the fallback UI
    return { hasError: true };
  }

  componentDidCatch(error, errorInfo) {
    // Log error to console (in production, send to error tracking service)
    console.error('[ErrorBoundary] Caught error:', error, errorInfo);

    this.setState({
      error,
      errorInfo,
    });

    // Send error to logging service (if available)
    if (typeof window !== 'undefined' && window.errorLogger) {
      window.errorLogger.log({
        error: error.toString(),
        componentStack: errorInfo.componentStack,
        timestamp: new Date().toISOString(),
      });
    }
  }

  handleReset = () => {
    this.setState({
      hasError: false,
      error: null,
      errorInfo: null,
    });
    // Optionally reload the page
    window.location.reload();
  };

  render() {
    if (this.state.hasError) {
      return (
        <div
          style={{
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            minHeight: '100vh',
            padding: '2rem',
            background: '#fafafa',
          }}
        >
          <div
            style={{
              textAlign: 'center',
              maxWidth: '480px',
              width: '100%',
            }}
          >
            {/* Error Icon */}
            <div
              style={{
                width: '80px',
                height: '80px',
                margin: '0 auto 32px',
                borderRadius: '50%',
                background: '#ff3b30',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                boxShadow: '0 8px 24px rgba(255, 59, 48, 0.2)',
              }}
            >
              <svg
                width="40"
                height="40"
                viewBox="0 0 24 24"
                fill="none"
                stroke="white"
                strokeWidth="2.5"
                strokeLinecap="round"
                strokeLinejoin="round"
              >
                <line x1="18" y1="6" x2="6" y2="18" />
                <line x1="6" y1="6" x2="18" y2="18" />
              </svg>
            </div>

            {/* Title */}
            <h1
              style={{
                fontSize: '24px',
                fontWeight: 600,
                color: '#1d1d1f',
                marginBottom: '12px',
                letterSpacing: '-0.02em',
              }}
            >
              문제가 발생했습니다
            </h1>

            {/* Description */}
            <p
              style={{
                fontSize: '15px',
                color: '#86868b',
                lineHeight: 1.6,
                marginBottom: '32px',
              }}
            >
              애플리케이션에서 예기치 않은 오류가 발생했습니다.
              <br />
              페이지가 고장났거나 삭제되었습니다. 다시 시도해보세요.
            </p>

            {/* Buttons */}
            <div style={{ display: 'flex', gap: '12px', justifyContent: 'center' }}>
              <Button
                type="primary"
                size="large"
                onClick={this.handleReset}
                style={{
                  height: '48px',
                  padding: '0 32px',
                  fontSize: '15px',
                  fontWeight: 500,
                  borderRadius: '12px',
                  background: '#0071e3',
                  border: 'none',
                }}
              >
                페이지 새로고침
              </Button>
              <Button
                size="large"
                onClick={() => (window.location.href = '/dashboard')}
                style={{
                  height: '48px',
                  padding: '0 32px',
                  fontSize: '15px',
                  fontWeight: 500,
                  borderRadius: '12px',
                  background: 'white',
                  border: '1px solid #d2d2d7',
                  color: '#1d1d1f',
                }}
              >
                대시보드로 이동
              </Button>
            </div>

            {/* Development Error Details */}
            {process.env.NODE_ENV === 'development' && this.state.error && (
              <div
                style={{
                  marginTop: '48px',
                  padding: '20px',
                  background: 'white',
                  borderRadius: '16px',
                  border: '1px solid #e8e8ed',
                  textAlign: 'left',
                }}
              >
                <h4
                  style={{
                    fontSize: '14px',
                    fontWeight: 600,
                    color: '#1d1d1f',
                    marginBottom: '12px',
                  }}
                >
                  개발 모드 에러 정보:
                </h4>
                <pre
                  style={{
                    fontSize: '12px',
                    overflow: 'auto',
                    color: '#515154',
                    lineHeight: 1.6,
                    margin: 0,
                  }}
                >
                  <strong>Error:</strong> {this.state.error.toString()}
                  {'\n\n'}
                  <strong>Component Stack:</strong>
                  {this.state.errorInfo?.componentStack}
                </pre>
              </div>
            )}
          </div>
        </div>
      );
    }

    return this.props.children;
  }
}

export default ErrorBoundary;
