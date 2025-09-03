export default function TermsPage() {
  return (
    <div className="min-h-screen bg-gradient-to-b from-gray-50 to-white">
      <div className="max-w-4xl mx-auto px-4 py-12">
        <div className="bg-white rounded-lg shadow-lg p-8">
          <h1 className="text-3xl font-bold bg-gradient-to-r from-blue-600 to-purple-600 bg-clip-text text-transparent mb-2">
            Terms of Service
          </h1>
          <p className="text-gray-600 mb-8">Effective Date: January 1, 2024</p>

          <div className="space-y-8 text-gray-700">
            <section>
              <h2 className="text-2xl font-semibold text-gray-900 mb-4">1. Acceptance of Terms</h2>
              <p className="leading-relaxed">
                By accessing and using the MapMyStandards platform ("Service"), you agree to be bound by these 
                Terms of Service ("Terms"). If you do not agree to these Terms, please do not use our Service. 
                These Terms apply to all visitors, users, and others who access or use the Service.
              </p>
            </section>

            <section>
              <h2 className="text-2xl font-semibold text-gray-900 mb-4">2. Description of Service</h2>
              <p className="mb-4">
                MapMyStandards provides an AI-powered compliance intelligence platform for educational institutions, 
                including but not limited to:
              </p>
              <ul className="list-disc pl-6 space-y-2">
                <li>StandardsGraph™ - Intelligent standards mapping and visualization</li>
                <li>EvidenceMapper™ - Automated evidence collection and mapping</li>
                <li>GapRisk Predictor™ - Predictive compliance gap analysis</li>
                <li>EvidenceTrust Score™ - Evidence quality assessment</li>
                <li>CrosswalkX™ - Multi-framework compliance mapping</li>
                <li>CiteGuard™ - Citation and reference management</li>
              </ul>
            </section>

            <section>
              <h2 className="text-2xl font-semibold text-gray-900 mb-4">3. User Accounts</h2>
              
              <h3 className="text-lg font-semibold text-gray-800 mb-2 mt-4">3.1 Registration</h3>
              <p>
                You must register for an account to use certain features of the Service. You agree to provide 
                accurate, current, and complete information during registration and to update such information 
                to keep it accurate, current, and complete.
              </p>

              <h3 className="text-lg font-semibold text-gray-800 mb-2 mt-4">3.2 Account Security</h3>
              <p>
                You are responsible for maintaining the confidentiality of your account credentials and for all 
                activities that occur under your account. You agree to notify us immediately of any unauthorized 
                use of your account or any other breach of security.
              </p>

              <h3 className="text-lg font-semibold text-gray-800 mb-2 mt-4">3.3 Account Restrictions</h3>
              <p>
                Accounts are intended for use by educational institutions and their authorized personnel only. 
                Sharing accounts across institutions is strictly prohibited.
              </p>
            </section>

            <section>
              <h2 className="text-2xl font-semibold text-gray-900 mb-4">4. Subscription and Payment</h2>
              
              <h3 className="text-lg font-semibold text-gray-800 mb-2 mt-4">4.1 Trial Period</h3>
              <p>
                We offer a 7-day free trial for new users. You may cancel at any time during the trial period 
                without charge. After the trial period, your subscription will automatically convert to a paid 
                subscription unless cancelled.
              </p>

              <h3 className="text-lg font-semibold text-gray-800 mb-2 mt-4">4.2 Subscription Plans</h3>
              <p className="mb-3">
                After the trial period, continued use of the Service requires a paid subscription. Current pricing:
              </p>
              <ul className="list-disc pl-6 space-y-2">
                <li>Standard Plan: $199 per month</li>
                <li>Professional Plan: Custom pricing</li>
                <li>Enterprise Plan: Custom pricing</li>
              </ul>

              <h3 className="text-lg font-semibold text-gray-800 mb-2 mt-4">4.3 Billing</h3>
              <p>
                Subscriptions are billed monthly in advance. You authorize us to charge your payment method on a 
                recurring basis. All payments are processed securely through Stripe.
              </p>

              <h3 className="text-lg font-semibold text-gray-800 mb-2 mt-4">4.4 Refunds</h3>
              <p>
                All sales are final. We do not offer refunds for partial months of service. You may cancel your 
                subscription at any time, and it will remain active until the end of your current billing period.
              </p>
            </section>

            <section>
              <h2 className="text-2xl font-semibold text-gray-900 mb-4">5. Acceptable Use</h2>
              <p className="mb-3">You agree not to:</p>
              <ul className="list-disc pl-6 space-y-2">
                <li>Use the Service for any unlawful purpose or in violation of any regulations</li>
                <li>Share your account with unauthorized users</li>
                <li>Attempt to reverse engineer, decompile, or compromise the Service</li>
                <li>Upload malicious content, viruses, or harmful software</li>
                <li>Interfere with or disrupt the Service or servers</li>
                <li>Collect or harvest data from the Service without permission</li>
                <li>Use the Service to infringe on intellectual property rights</li>
                <li>Misrepresent your affiliation with an educational institution</li>
              </ul>
            </section>

            <section>
              <h2 className="text-2xl font-semibold text-gray-900 mb-4">6. Intellectual Property</h2>
              
              <h3 className="text-lg font-semibold text-gray-800 mb-2 mt-4">6.1 Our Property</h3>
              <p>
                All content, features, and functionality of the Service, including but not limited to text, 
                graphics, logos, icons, images, audio clips, digital downloads, data compilations, and software, 
                are owned by MapMyStandards and are protected by copyright, trademark, and other intellectual 
                property laws.
              </p>

              <h3 className="text-lg font-semibold text-gray-800 mb-2 mt-4">6.2 Your Content</h3>
              <p>
                You retain ownership of any content you upload to the Service. By uploading content, you grant 
                us a non-exclusive, worldwide, royalty-free license to use, reproduce, modify, and distribute 
                your content solely for the purpose of providing and improving the Service.
              </p>

              <h3 className="text-lg font-semibold text-gray-800 mb-2 mt-4">6.3 Feedback</h3>
              <p>
                Any feedback, suggestions, or ideas you provide about the Service may be used by us without any 
                obligation to compensate you.
              </p>
            </section>

            <section>
              <h2 className="text-2xl font-semibold text-gray-900 mb-4">7. Data Privacy and Security</h2>
              <p>
                Your use of the Service is also governed by our Privacy Policy. We take data security seriously 
                and implement industry-standard measures to protect your information. However, no method of 
                transmission over the Internet is 100% secure, and we cannot guarantee absolute security.
              </p>
            </section>

            <section>
              <h2 className="text-2xl font-semibold text-gray-900 mb-4">8. AI and Automated Processing</h2>
              <p>
                Our Service uses artificial intelligence and machine learning algorithms to analyze compliance 
                documents and generate insights. While we strive for accuracy, AI-generated content should be 
                reviewed by qualified professionals and should not be relied upon as the sole basis for compliance 
                decisions.
              </p>
            </section>

            <section>
              <h2 className="text-2xl font-semibold text-gray-900 mb-4">9. Disclaimers</h2>
              
              <h3 className="text-lg font-semibold text-gray-800 mb-2 mt-4">9.1 "As Is" Service</h3>
              <p>
                The Service is provided "as is" and "as available" without warranties of any kind, either express 
                or implied, including but not limited to implied warranties of merchantability, fitness for a 
                particular purpose, and non-infringement.
              </p>

              <h3 className="text-lg font-semibold text-gray-800 mb-2 mt-4">9.2 No Professional Advice</h3>
              <p>
                The Service does not constitute professional accreditation advice. You should consult with 
                qualified accreditation professionals for specific compliance guidance.
              </p>
            </section>

            <section>
              <h2 className="text-2xl font-semibold text-gray-900 mb-4">10. Limitation of Liability</h2>
              <p>
                To the fullest extent permitted by law, MapMyStandards shall not be liable for any indirect, 
                incidental, special, consequential, or punitive damages, including but not limited to loss of 
                profits, data, use, goodwill, or other intangible losses, arising from your use of the Service.
              </p>
            </section>

            <section>
              <h2 className="text-2xl font-semibold text-gray-900 mb-4">11. Indemnification</h2>
              <p>
                You agree to indemnify, defend, and hold harmless MapMyStandards and its officers, directors, 
                employees, and agents from any claims, liabilities, damages, losses, and expenses, including 
                reasonable attorney's fees, arising from your use of the Service or violation of these Terms.
              </p>
            </section>

            <section>
              <h2 className="text-2xl font-semibold text-gray-900 mb-4">12. Termination</h2>
              <p>
                We may terminate or suspend your account at any time for violations of these Terms, with or 
                without notice. You may cancel your subscription at any time through your account settings. 
                Upon termination, your right to use the Service will immediately cease.
              </p>
            </section>

            <section>
              <h2 className="text-2xl font-semibold text-gray-900 mb-4">13. Changes to Terms</h2>
              <p>
                We reserve the right to modify these Terms at any time. We will notify users of any material 
                changes via email or through the Service. Your continued use of the Service after such 
                modifications constitutes your acceptance of the updated Terms.
              </p>
            </section>

            <section>
              <h2 className="text-2xl font-semibold text-gray-900 mb-4">14. Governing Law</h2>
              <p>
                These Terms shall be governed by and construed in accordance with the laws of the United States, 
                without regard to its conflict of law provisions. Any legal action or proceeding arising under 
                these Terms will be brought exclusively in the federal or state courts located in the United States.
              </p>
            </section>

            <section>
              <h2 className="text-2xl font-semibold text-gray-900 mb-4">15. Entire Agreement</h2>
              <p>
                These Terms, together with our Privacy Policy, constitute the entire agreement between you and 
                MapMyStandards regarding the use of the Service and supersede all prior agreements and understandings.
              </p>
            </section>

            <section>
              <h2 className="text-2xl font-semibold text-gray-900 mb-4">16. Contact Information</h2>
              <p className="mb-4">
                For questions about these Terms of Service, please contact us at:
              </p>
              <div className="bg-gray-50 p-4 rounded-lg">
                <p className="font-semibold">MapMyStandards</p>
                <p>Email: legal@mapmystandards.ai</p>
                <p>Support: support@mapmystandards.ai</p>
                <p>Website: https://mapmystandards.ai</p>
              </div>
            </section>
          </div>
        </div>
      </div>
    </div>
  );
}