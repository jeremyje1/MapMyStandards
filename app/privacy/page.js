export default function PrivacyPage() {
  return (
    <div className="min-h-screen bg-gradient-to-b from-gray-50 to-white">
      <div className="max-w-4xl mx-auto px-4 py-12">
        <div className="bg-white rounded-lg shadow-lg p-8">
          <h1 className="text-3xl font-bold bg-gradient-to-r from-blue-600 to-purple-600 bg-clip-text text-transparent mb-2">
            Privacy Policy
          </h1>
          <p className="text-gray-600 mb-8">Effective Date: January 1, 2024</p>

          <div className="space-y-8 text-gray-700">
            <section>
              <h2 className="text-2xl font-semibold text-gray-900 mb-4">1. Introduction</h2>
              <p className="leading-relaxed">
                MapMyStandards ("we," "our," or "us") is committed to protecting your privacy. This Privacy Policy 
                explains how we collect, use, disclose, and safeguard your information when you use our compliance 
                intelligence platform, including our StandardsGraph™, EvidenceMapper™, and related services.
              </p>
            </section>

            <section>
              <h2 className="text-2xl font-semibold text-gray-900 mb-4">2. Information We Collect</h2>
              
              <h3 className="text-lg font-semibold text-gray-800 mb-2 mt-4">2.1 Personal Information</h3>
              <p className="mb-3">We collect information you provide directly to us, including:</p>
              <ul className="list-disc pl-6 space-y-2">
                <li>Name and contact information (email, phone number)</li>
                <li>Institution name and role</li>
                <li>Account credentials</li>
                <li>Payment information (processed securely through Stripe)</li>
                <li>Communications with our support team</li>
              </ul>

              <h3 className="text-lg font-semibold text-gray-800 mb-2 mt-4">2.2 Usage Information</h3>
              <p className="mb-3">We automatically collect certain information about your use of the Service:</p>
              <ul className="list-disc pl-6 space-y-2">
                <li>Log data (IP address, browser type, access times)</li>
                <li>Device information</li>
                <li>Usage patterns and preferences</li>
                <li>Performance metrics</li>
              </ul>

              <h3 className="text-lg font-semibold text-gray-800 mb-2 mt-4">2.3 Document Information</h3>
              <p>
                When you upload compliance documents for analysis, we process and store these documents securely. 
                Our AI algorithms analyze content to provide compliance insights, but we maintain strict confidentiality 
                of your institutional data.
              </p>
            </section>

            <section>
              <h2 className="text-2xl font-semibold text-gray-900 mb-4">3. How We Use Your Information</h2>
              <p className="mb-3">We use the collected information to:</p>
              <ul className="list-disc pl-6 space-y-2">
                <li>Provide and maintain the Service</li>
                <li>Process transactions and billing</li>
                <li>Send administrative communications</li>
                <li>Improve and personalize the Service</li>
                <li>Provide customer support</li>
                <li>Ensure security and prevent fraud</li>
                <li>Comply with legal obligations</li>
                <li>Generate compliance insights and recommendations</li>
              </ul>
            </section>

            <section>
              <h2 className="text-2xl font-semibold text-gray-900 mb-4">4. Data Security</h2>
              <p className="mb-3">
                We implement appropriate technical and organizational measures to protect your information, including:
              </p>
              <ul className="list-disc pl-6 space-y-2">
                <li>Encryption of data in transit and at rest</li>
                <li>Regular security audits</li>
                <li>Access controls and authentication</li>
                <li>Regular backups</li>
                <li>Secure cloud infrastructure (Railway, Vercel)</li>
                <li>Compliance with industry standards</li>
              </ul>
            </section>

            <section>
              <h2 className="text-2xl font-semibold text-gray-900 mb-4">5. Data Sharing</h2>
              <p className="mb-3">
                We do not sell, trade, or rent your personal information. We may share your information only in the 
                following circumstances:
              </p>
              <ul className="list-disc pl-6 space-y-2">
                <li>With your consent</li>
                <li>To comply with legal obligations</li>
                <li>To protect our rights and prevent fraud</li>
                <li>With service providers who assist in our operations (under strict confidentiality agreements)</li>
              </ul>
            </section>

            <section>
              <h2 className="text-2xl font-semibold text-gray-900 mb-4">6. Your Rights</h2>
              <p className="mb-3">You have the right to:</p>
              <ul className="list-disc pl-6 space-y-2">
                <li>Access your personal information</li>
                <li>Correct inaccurate information</li>
                <li>Request deletion of your information</li>
                <li>Export your data</li>
                <li>Opt-out of marketing communications</li>
                <li>Request restrictions on processing</li>
              </ul>
            </section>

            <section>
              <h2 className="text-2xl font-semibold text-gray-900 mb-4">7. Cookies and Tracking</h2>
              <p>
                We use cookies and similar tracking technologies to enhance your experience. You can control cookie 
                preferences through your browser settings. Essential cookies are required for the platform to function 
                properly.
              </p>
            </section>

            <section>
              <h2 className="text-2xl font-semibold text-gray-900 mb-4">8. Data Retention</h2>
              <p>
                We retain your information for as long as necessary to provide our services and comply with legal 
                obligations. You may request deletion of your account and associated data at any time.
              </p>
            </section>

            <section>
              <h2 className="text-2xl font-semibold text-gray-900 mb-4">9. Children's Privacy</h2>
              <p>
                Our Service is not intended for individuals under the age of 18. We do not knowingly collect personal 
                information from children.
              </p>
            </section>

            <section>
              <h2 className="text-2xl font-semibold text-gray-900 mb-4">10. Changes to This Policy</h2>
              <p>
                We may update this Privacy Policy from time to time. We will notify you of any material changes via 
                email or through the Service. Your continued use of the Service after such modifications constitutes 
                your acceptance of the updated Privacy Policy.
              </p>
            </section>

            <section>
              <h2 className="text-2xl font-semibold text-gray-900 mb-4">11. Contact Us</h2>
              <p className="mb-4">
                For questions about this Privacy Policy or our data practices, please contact us at:
              </p>
              <div className="bg-gray-50 p-4 rounded-lg">
                <p className="font-semibold">MapMyStandards</p>
                <p>Email: privacy@mapmystandards.ai</p>
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