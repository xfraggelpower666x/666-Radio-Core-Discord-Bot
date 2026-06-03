/**
 * 666RadioCoreDJ | src/discord/commands.js
 * Erstellt: 2026-06-03
 * Geändert: 2026-06-03
 * Zweck: Slash-Command-Definitionen für /radio sowie direkten Voice-Stream über /play, /pause, /resume, /stop und /volume.
 * Änderung v1.3.0: Pause/Resume, 5 Stream-Presets über /play preset und Lautstärke-/Default-Option über /volume ergänzt.
 */
const { SlashCommandBuilder } = require('discord.js');

const radioCommand = new SlashCommandBuilder()
  .setName('radio')
  .setDescription('666RadioCoreDJ Steuerung')
  .addSubcommand((sub) => sub
    .setName('panel')
    .setDescription('Postet das 666RadioCoreDJ Button-Panel in den aktuellen Kanal.'))
  .addSubcommand((sub) => sub
    .setName('status')
    .setDescription('Zeigt den aktuellen Bot-/Adapterstatus ohne Secrets.'))
  .addSubcommand((sub) => sub
    .setName('skip')
    .setDescription('Überspringt den aktuellen AutoDJ-Track über SonicPanel/MyIDJ.'))
  .addSubcommand((sub) => sub
    .setName('jingle')
    .setDescription('Spielt einen vorbereiteten SonicPanel Jingle/ID On-Air.')
    .addStringOption((option) => option
      .setName('name')
      .setDescription('Jingle-/ID-Name oder ID entsprechend SonicPanel-Konfiguration.')
      .setRequired(true)));

const playCommand = new SlashCommandBuilder()
  .setName('play')
  .setDescription('Startet einen Radiostream im Voice-Channel, in dem du gerade bist.')
  .addStringOption((option) => option
    .setName('preset')
    .setDescription('Stream-Preset: 1-5 oder Preset-Name. Leer = Default-Preset.')
    .setRequired(false)
    .addChoices(
      { name: 'Preset 1', value: '1' },
      { name: 'Preset 2', value: '2' },
      { name: 'Preset 3', value: '3' },
      { name: 'Preset 4', value: '4' },
      { name: 'Preset 5', value: '5' }
    ));

const pauseCommand = new SlashCommandBuilder()
  .setName('pause')
  .setDescription('Pausiert den Voice-Stream, lässt den Bot aber im Voice-Channel.');

const resumeCommand = new SlashCommandBuilder()
  .setName('resume')
  .setDescription('Setzt den pausierten Voice-Stream live fort.');

const stopCommand = new SlashCommandBuilder()
  .setName('stop')
  .setDescription('Stoppt den 666RadioCoreDJ Voice-Stream und trennt den Bot vom Voice-Channel.');

const volumeCommand = new SlashCommandBuilder()
  .setName('volume')
  .setDescription('Zeigt oder setzt die Voice-Stream-Lautstärke.')
  .addIntegerOption((option) => option
    .setName('level')
    .setDescription('Lautstärke in Prozent. Beispiel: 80, 100, 125. Leer = nur anzeigen.')
    .setRequired(false)
    .setMinValue(0)
    .setMaxValue(200))
  .addBooleanOption((option) => option
    .setName('default')
    .setDescription('Auf VOICE_DEFAULT_VOLUME_PERCENT zurücksetzen.')
    .setRequired(false));

module.exports = {
  commands: [
    radioCommand.toJSON(),
    playCommand.toJSON(),
    pauseCommand.toJSON(),
    resumeCommand.toJSON(),
    stopCommand.toJSON(),
    volumeCommand.toJSON()
  ]
};
