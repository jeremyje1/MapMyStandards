import NextAuth, { NextAuthOptions } from 'next-auth';
import EmailProvider from 'next-auth/providers/email';
import { sendEmail } from '@/lib/email/postmark';

// Base URL for magic links
const baseUrl = process.env.NEXT_PUBLIC_APP_URL || 'http://localhost:3000';

const authOptions: NextAuthOptions = {
  providers: [
    EmailProvider({
      async sendVerificationRequest({ identifier, url /*, provider */ }) {
        // identifier is the email address
        const signInUrl = url; // Provided by NextAuth
        await sendEmail({
          to: identifier,
          subject: 'Your secure sign-in link',
          html: `
            <p>Click the button to sign in:</p>
            <p><a href="${signInUrl}" style="display:inline-block;padding:10px 16px;border-radius:6px;background:#1f2937;color:#fff;text-decoration:none;">Sign in</a></p>
            <p>Or paste this URL in your browser:<br>${signInUrl}</p>
          `,
          text: `Sign in: ${signInUrl}`,
          tag: 'magic-link',
        });
      },
      from: process.env.FROM_EMAIL,
      maxAge: 60 * 30, // Magic link valid 30 minutes
    }),
  ],
  session: {
    strategy: 'jwt',
    maxAge: 60 * 60 * 24 * 30, // 30 days
  },
  pages: {
    signIn: '/auth/signin',
    verifyRequest: '/auth/verify-request',
    error: '/auth/error',
  },
  callbacks: {
    async jwt({ token, user }) {
      // Attach tier/role in future; placeholder
      if (user) {
        // token.role = user.role
      }
      return token;
    },
    async session({ session, token }) {
      // session.user.role = token.role
      return session;
    },
  },
};

const handler = NextAuth(authOptions);
export { handler as GET, handler as POST };