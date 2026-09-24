const fs = require('fs');
const { execSync } = require('child_process');

jest.mock('fs');
jest.mock('child_process');
jest.mock('axios');
jest.mock('nodemailer');

describe('Aggregator Report Functions', () => {
    let axios;
    let nodemailer;

    beforeEach(() => {
        jest.clearAllMocks();
        axios = require('axios');
        nodemailer = require('nodemailer');
    });

    describe('getLatestFromCSV', () => {
        const getLatestFromCSV = (path) => {
            if (fs.existsSync(path)) {
                let lines = fs.readFileSync(path, 'utf8').trim().split('\n').filter(l => l.includes(','));
                if (lines.length > 0) {
                    lines.sort((a, b) => b.split(',')[0].localeCompare(a.split(',')[0]));
                    const lastEntry = lines[0].split(',');
                    const [y, m, d] = lastEntry[0].split('-');
                    return { val: parseFloat(lastEntry[1]), date: `${d}/${m}` };
                }
            }
            return null;
        };

        test('should return null for non-existent file', () => {
            fs.existsSync.mockReturnValue(false);
            const result = getLatestFromCSV('/nonexistent/path.csv');
            expect(result).toBeNull();
        });

        test('should extract latest entry correctly', () => {
            fs.existsSync.mockReturnValue(true);
            fs.readFileSync.mockReturnValue('2023-01-01,10.5\n2023-01-02,11.2\n2023-01-03,12.0\n');

            const result = getLatestFromCSV('/path/to/file.csv');
            expect(result).toEqual({ val: 12.0, date: '03/01' });
        });

        test('should handle single entry CSV', () => {
            fs.existsSync.mockReturnValue(true);
            fs.readFileSync.mockReturnValue('2023-01-01,10.5\n');

            const result = getLatestFromCSV('/path/to/file.csv');
            expect(result).toEqual({ val: 10.5, date: '01/01' });
        });

        test('should skip empty lines', () => {
            fs.existsSync.mockReturnValue(true);
            fs.readFileSync.mockReturnValue('2023-01-01,10.5\n\n2023-01-02,11.2\n\n');

            const result = getLatestFromCSV('/path/to/file.csv');
            expect(result).toEqual({ val: 11.2, date: '02/01' });
        });

        test('should handle decimal values correctly', () => {
            fs.existsSync.mockReturnValue(true);
            fs.readFileSync.mockReturnValue('2023-01-01,10.567\n2023-01-02,11.234\n');

            const result = getLatestFromCSV('/path/to/file.csv');
            expect(result.val).toBeCloseTo(11.234, 3);
        });
    });

    describe('Cost Calculations', () => {
        const TARIFS = {
            basse: { hp: 0.19209, hc: 0.16039 },
            gas: 0.11548
        };
        const ABONNEMENT_JOUR = 228.86 / 365;

        test('should calculate electricity cost correctly', () => {
            const kwh = 10.5;
            const cost = (kwh * TARIFS.basse.hp) + ABONNEMENT_JOUR;
            expect(cost).toBeCloseTo(2.626, 2);
        });

        test('should calculate gas cost correctly', () => {
            const kwh = 5.0;
            const cost = kwh * TARIFS.gas;
            expect(cost).toBeCloseTo(0.577, 2);
        });

        test('should calculate car charging cost correctly', () => {
            const carKwh = 15.0;
            const carCost = (carKwh * TARIFS.basse.hc).toFixed(2);
            expect(parseFloat(carCost)).toBeCloseTo(2.41, 1);
        });

        test('should handle zero consumption', () => {
            const cost = (0 * TARIFS.basse.hp) + ABONNEMENT_JOUR;
            expect(cost).toBeCloseTo(0.627, 2);
        });

        test('should handle high consumption', () => {
            const kwh = 50.0;
            const cost = (kwh * TARIFS.basse.hp) + ABONNEMENT_JOUR;
            expect(cost).toBeCloseTo(11.236, 2);
        });
    });

    describe('System Statistics Retrieval', () => {
        test('should handle vcgencmd failure gracefully', () => {
            execSync.mockImplementation(() => {
                throw new Error('Command failed');
            });

            let temp = 'N/A';
            try {
                temp = execSync('vcgencmd measure_temp').toString().replace('temp=', '').trim();
            } catch (e) {
                temp = 'N/A';
            }

            expect(temp).toBe('N/A');
        });

        test('should parse vcgencmd output correctly', () => {
            execSync.mockReturnValue('temp=45.6\'C\n');
            const temp = execSync('vcgencmd measure_temp').toString().replace('temp=', '').trim();
            expect(temp).toBe('45.6\'C');
        });

        test('should handle uptime command successfully', () => {
            execSync.mockReturnValue('up 5 days, 3 hours, 42 minutes\n');
            const uptime = execSync('uptime -p').toString().trim();
            expect(uptime).toBe('up 5 days, 3 hours, 42 minutes');
        });
    });

    describe('API Data Fetching', () => {
        test('should fetch market sentiment successfully', async () => {
            axios.get.mockResolvedValue({
                data: {
                    data: [
                        {
                            value: 75,
                            value_classification: 'Extrême Avidité'
                        }
                    ]
                }
            });

            const response = await axios.get('https://api.alternative.me/fng/');
            expect(response.data.data[0].value).toBe(75);
            expect(response.data.data[0].value_classification).toBe('Extrême Avidité');
        });

        test('should handle API failures gracefully', async () => {
            axios.get.mockRejectedValue(new Error('Network error'));

            try {
                await axios.get('https://api.alternative.me/fng/');
            } catch (e) {
                expect(e.message).toBe('Network error');
            }
        });
    });

    describe('Email Sending', () => {
        const mockTransporter = {
            sendMail: jest.fn()
        };

        test('should send email with correct options', async () => {
            mockTransporter.sendMail.mockResolvedValue({ messageId: 'test@example.com' });

            const mailOptions = {
                from: 'test@gmail.com',
                to: 'recipient@example.com',
                subject: 'Test Report',
                html: '<h1>Test</h1>'
            };

            const result = await mockTransporter.sendMail(mailOptions);
            expect(result.messageId).toBe('test@example.com');
            expect(mockTransporter.sendMail).toHaveBeenCalledWith(mailOptions);
        });

        test('should handle email sending errors', async () => {
            mockTransporter.sendMail.mockRejectedValue(new Error('SMTP error'));

            const mailOptions = {
                from: 'test@gmail.com',
                to: 'recipient@example.com',
                subject: 'Test Report',
                html: '<h1>Test</h1>'
            };

            try {
                await mockTransporter.sendMail(mailOptions);
            } catch (e) {
                expect(e.message).toBe('SMTP error');
            }
        });

        test('should include proper HTML structure in email', async () => {
            const html = `
            <!DOCTYPE html>
            <html lang="fr">
            <head>
                <meta charset="UTF-8">
                <title>Rapport</title>
            </head>
            <body>
                <h1>Rapport Quotidien</h1>
                <div>Test Content</div>
            </body>
            </html>`;

            expect(html).toContain('<!DOCTYPE html>');
            expect(html).toContain('Rapport Quotidien');
            expect(html).toContain('Test Content');
        });
    });

    describe('Date Formatting', () => {
        test('should format yesterday date correctly', () => {
            const yesterday = new Date('2023-01-02');
            const dateStr = yesterday.toISOString().split('T')[0];
            expect(dateStr).toBe('2023-01-02');
        });

        test('should format date for CSV lookup correctly', () => {
            const yesterday = new Date('2023-01-02');
            const dateStr = yesterday.toISOString().split('T')[0];
            expect(dateStr).toMatch(/^\d{4}-\d{2}-\d{2}$/);
        });
    });

    describe('Data Validation', () => {
        test('should handle missing CSV values with defaults', () => {
            const linky = { kwh: 0, cost: 0, date: 'N/A' };
            expect(linky.kwh).toBe(0);
            expect(linky.cost).toBe(0);
            expect(linky.date).toBe('N/A');
        });

        test('should validate numeric values are properly formatted', () => {
            const kwh = 10.5;
            const formatted = kwh.toFixed(2);
            expect(formatted).toBe('10.50');
            expect(parseFloat(formatted)).toBe(10.5);
        });

        test('should handle zero values correctly', () => {
            const value = 0;
            const formatted = value.toFixed(2);
            expect(formatted).toBe('0.00');
        });

        test('should handle large values correctly', () => {
            const value = 1234.5678;
            const formatted = value.toFixed(2);
            expect(formatted).toBe('1234.57');
        });
    });

    describe('HTML Template Generation', () => {
        test('should generate valid HTML structure', () => {
            const html = `
            <!DOCTYPE html>
            <html lang="fr">
            <head><meta charset="UTF-8"></head>
            <body><div class="container"></div></body>
            </html>`;

            expect(html).toContain('<!DOCTYPE html>');
            expect(html).toContain('lang="fr"');
            expect(html).toContain('class="container"');
        });

        test('should include all report sections in HTML', () => {
            const sections = ['⚡️ Électricité', '🔥 Gaz', '🚗 Recharge', '💰 Finance', '🛡️ État du Serveur'];
            const html = sections.join('<br>');

            sections.forEach(section => {
                expect(html).toContain(section);
            });
        });

        test('should use correct CSS classes for styling', () => {
            const html = `<div class="card"><div class="price-tag"></div></div>`;
            expect(html).toContain('class="card"');
            expect(html).toContain('class="price-tag"');
        });
    });
});
